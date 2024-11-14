from ninja import Schema


class AddCommentSchema(Schema):
    topic_slug: str
    comment: str


class AddReplyToCommentSchema(Schema):
    comment_id: str
    reply: str


class AddNewPostSchema(Schema):
    title: str
    body: str
    community: str


class AddNewCommunitySchema(Schema):
    name: str
    description: str
