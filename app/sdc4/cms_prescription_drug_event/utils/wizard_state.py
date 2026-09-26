"""
Wizard State Management for multi-step form data entry.

This module manages the state of the wizard across HTTP requests using
Django sessions. It stores partial data from each step and coordinates
the final XML generation.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from django.utils import timezone
import json

logger = logging.getLogger(__name__)


@dataclass
class WizardStepData:
    """Data collected from a single wizard step."""
    completed: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None

    def mark_complete(self):
        self.completed = True
        self.timestamp = timezone.now().isoformat()


@dataclass
class WizardStateData:
    """Complete wizard state across all steps."""
    current_step: int = 0
    instance_id: Optional[str] = None
    step_0_setup: WizardStepData = field(default_factory=WizardStepData)
    step_1_context: WizardStepData = field(default_factory=WizardStepData)
    step_2_data: WizardStepData = field(default_factory=WizardStepData)
    step_3_review: WizardStepData = field(default_factory=WizardStepData)
    started_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for session storage."""
        return {
            'current_step': self.current_step,
            'instance_id': self.instance_id,
            'step_0_setup': asdict(self.step_0_setup),
            'step_1_context': asdict(self.step_1_context),
            'step_2_data': asdict(self.step_2_data),
            'step_3_review': asdict(self.step_3_review),
            'started_at': self.started_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WizardStateData':
        """Create from dictionary (session storage)."""
        return cls(
            current_step=data.get('current_step', 0),
            instance_id=data.get('instance_id'),
            step_0_setup=WizardStepData(**data.get('step_0_setup', {})),
            step_1_context=WizardStepData(**data.get('step_1_context', {})),
            step_2_data=WizardStepData(**data.get('step_2_data', {})),
            step_3_review=WizardStepData(**data.get('step_3_review', {})),
            started_at=data.get('started_at'),
        )


class WizardState:
    """
    Manages wizard state across HTTP requests using Django sessions.

    Usage:
        # In view
        wizard = WizardState(request)

        # Get current step
        step = wizard.get_current_step()

        # Save step data
        wizard.save_step_data(step, form.cleaned_data)

        # Move to next step
        wizard.next_step()

        # Build final XML
        xml_content = wizard.build_xml()

        # Clear state after successful save
        wizard.clear()
    """

    SESSION_KEY = 'cms_prescription_drug_event_wizard_state'

    def __init__(self, request):
        """
        Initialize wizard state from session.

        Args:
            request: Django HttpRequest object
        """
        self.request = request
        self._load_state()

    def _load_state(self):
        """Load state from session or create new."""
        session_data = self.request.session.get(self.SESSION_KEY)
        if session_data:
            self.state = WizardStateData.from_dict(session_data)
        else:
            self.state = WizardStateData(
                started_at=timezone.now().isoformat()
            )

    def save(self):
        """Persist state to session."""
        self.request.session[self.SESSION_KEY] = self.state.to_dict()
        self.request.session.modified = True

    def clear(self):
        """Clear wizard state from session."""
        if self.SESSION_KEY in self.request.session:
            del self.request.session[self.SESSION_KEY]
            self.request.session.modified = True
        self.state = WizardStateData(started_at=timezone.now().isoformat())

    # =========================================================================
    # Step Navigation
    # =========================================================================

    def get_current_step(self) -> int:
        """Get current step number."""
        return self.state.current_step

    def set_current_step(self, step: int):
        """Set current step number."""
        self.state.current_step = step
        self.save()

    def next_step(self):
        """Move to next step."""
        self.state.current_step += 1
        self.save()

    def prev_step(self):
        """Move to previous step."""
        if self.state.current_step > 0:
            self.state.current_step -= 1
            self.save()

    def can_proceed_to_step(self, step: int) -> bool:
        """
        Check if user can proceed to a given step.

        All previous steps must be completed (or skipped if conditional).
        """
        if step == 0:
            return True

        # Check all previous steps
        for i in range(step):
            step_data = self._get_step_data(i)
            if step_data and not step_data.completed:
                # Check if step is conditional and can be skipped
                if not self._is_step_conditional(i):
                    return False

        return True

    def _is_step_conditional(self, step: int) -> bool:
        """Check if a step is conditional (can be skipped)."""
        # Step 1 (Context) and Step 3 (Review) are conditional
        # based on DM configuration
        from .wizard_config import WizardStepConfig
        if step == 1:
            return not WizardStepConfig.show_context_step()
        if step == 3:
            return not WizardStepConfig.show_attestation_step()
        return False

    # =========================================================================
    # Step Data Management
    # =========================================================================

    def _get_step_data(self, step: int) -> Optional[WizardStepData]:
        """Get step data object by step number."""
        step_map = {
            0: self.state.step_0_setup,
            1: self.state.step_1_context,
            2: self.state.step_2_data,
            3: self.state.step_3_review,
        }
        return step_map.get(step)

    def get_step_data(self, step: int) -> Dict[str, Any]:
        """Get data dictionary for a step."""
        step_data = self._get_step_data(step)
        return step_data.data if step_data else {}

    def save_step_data(self, step: int, data: Dict[str, Any], complete: bool = True):
        """
        Save data for a step.

        Args:
            step: Step number (0-3)
            data: Form data dictionary
            complete: Whether to mark step as completed
        """
        step_data = self._get_step_data(step)
        if step_data:
            step_data.data = data
            if complete:
                step_data.mark_complete()
            self.save()

    def is_step_complete(self, step: int) -> bool:
        """Check if a step is completed."""
        step_data = self._get_step_data(step)
        return step_data.completed if step_data else False

    # =========================================================================
    # Instance ID Management
    # =========================================================================

    def get_instance_id(self) -> Optional[str]:
        """Get the instance ID for this wizard session."""
        return self.state.instance_id

    def set_instance_id(self, instance_id: str):
        """Set the instance ID."""
        self.state.instance_id = instance_id
        self.save()

    def generate_instance_id(self) -> str:
        """Generate a new instance ID if not already set."""
        if not self.state.instance_id:
            from cuid2 import cuid_wrapper
            cuid_generator = cuid_wrapper()
            self.state.instance_id = f"i-{cuid_generator()}"
            self.save()
        return self.state.instance_id

    # =========================================================================
    # XML Building
    # =========================================================================

    def get_all_data(self) -> Dict[str, Any]:
        """
        Get all wizard data combined for XML building.

        Returns:
            Dictionary with all step data merged
        """
        return {
            'instance_id': self.state.instance_id,
            'setup': self.state.step_0_setup.data,
            'context': self.state.step_1_context.data,
            'data': self.state.step_2_data.data,
            'review': self.state.step_3_review.data,
        }

    def build_xml(self) -> str:
        """
        Build complete XML from all wizard data.

        Returns:
            Complete SDC4 XML instance string
        """
        from .xml_builder import XMLBuilder
        from .wizard_config import FIELD_METADATA, DMMetadata

        all_data = self.get_all_data()
        instance_id = self.generate_instance_id()

        builder = XMLBuilder(
            dm_ct_id=DMMetadata.CT_ID,
            dm_label=DMMetadata.TITLE,
            field_metadata=FIELD_METADATA
        )
        return builder.build_from_wizard(instance_id, all_data)

    # =========================================================================
    # Debugging
    # =========================================================================

    def debug_info(self) -> Dict[str, Any]:
        """Get debug information about wizard state."""
        return {
            'current_step': self.state.current_step,
            'instance_id': self.state.instance_id,
            'started_at': self.state.started_at,
            'steps': {
                0: {'completed': self.state.step_0_setup.completed,
                    'has_data': bool(self.state.step_0_setup.data)},
                1: {'completed': self.state.step_1_context.completed,
                    'has_data': bool(self.state.step_1_context.data)},
                2: {'completed': self.state.step_2_data.completed,
                    'has_data': bool(self.state.step_2_data.data)},
                3: {'completed': self.state.step_3_review.completed,
                    'has_data': bool(self.state.step_3_review.data)},
            }
        }
