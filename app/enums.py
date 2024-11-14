from enum import Enum


class RoleTypeEnum(Enum):

    WRITER = "WRITER"
    READER = "READER"


class GenderEnum(Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class StartReadingChapter(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class RewardType(Enum):
    DAILY_REWARD = 1
    DAILY_20_SOCIAL_POST = 10
    FINISH_READING_A_BOOK = 20
    DAILY_20_FORUMS_POST = 10
    INVITE_FRIENDS = 20


class PlagiarismCheckerStatus(Enum):
    STATE_STORED = "Text has been stored and waiting for a check."
    STATE_SUBMITTED = "Text has been submitted and waiting for a check."
    STATE_FAILED = "Text has not been checked. An error happened."
    STATE_CHECKED = "Text has been successfully checked and you can receive the report."


plagiarism_checker_state = {
    2: "STATE_STORED",
    3: "STATE_SUBMITTED",
    4: "STATE_FAILED",
    5: "STATE_CHECKED",
}
