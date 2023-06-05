from __future__ import annotations

from sentry.eventstore.models import Event
from sentry.issues.grouptype import GroupCategory
from sentry.utils.safe import get_path, set_path
from sentry.utils.sdk_crashes.cocoa_sdk_crash_detector import CocoaSDKCrashDetector
from sentry.utils.sdk_crashes.event_stripper import strip_event_data
from sentry.utils.sdk_crashes.sdk_crash_detector import SDKCrashDetector


class SDKCrashReporter:
    def __init__(self):
        self

    def report(self, event: Event) -> None:
        return


class SDKCrashDetection:
    def __init__(
        self,
        sdk_crash_reporter: SDKCrashReporter,
        sdk_crash_detector: SDKCrashDetector,
    ):
        self
        self.sdk_crash_reporter = sdk_crash_reporter
        self.cocoa_sdk_crash_detector = sdk_crash_detector

    def detect_sdk_crash(self, event: Event) -> None:

        should_detect_sdk_crash = (
            event.group
            and event.group.issue_category == GroupCategory.ERROR
            and event.group.platform == "cocoa"
        )
        if not should_detect_sdk_crash:
            return

        context = get_path(event.data, "contexts", "sdk_crash_detection")
        if context is not None and context.get("detected", False):
            return

        is_unhandled = (
            get_path(event.data, "exception", "values", -1, "mechanism", "data", "handled") is False
        )
        if is_unhandled is False:
            return

        frames = get_path(event.data, "exception", "values", -1, "stacktrace", "frames")
        if not frames:
            return

        if self.cocoa_sdk_crash_detector.is_sdk_crash(frames):
            sdk_crash_event = strip_event_data(event, self.cocoa_sdk_crash_detector)

            set_path(
                sdk_crash_event.data, "contexts", "sdk_crash_detection", value={"detected": True}
            )
            self.sdk_crash_reporter.report(sdk_crash_event)


_crash_reporter = SDKCrashReporter()
_cocoa_sdk_crash_detector = CocoaSDKCrashDetector()

sdk_crash_detection = SDKCrashDetection(_crash_reporter, _cocoa_sdk_crash_detector)