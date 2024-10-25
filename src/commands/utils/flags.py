import hikari

# Response types
DEFERRED_CREATE = hikari.ResponseType.DEFERRED_MESSAGE_CREATE
DEFERRED_UPDATE = hikari.ResponseType.DEFERRED_MESSAGE_UPDATE

# Message flags
LOADING = hikari.MessageFlag.LOADING
EPHEMERAL = hikari.MessageFlag.EPHEMERAL
LOADING_EPHEMERAL = LOADING | EPHEMERAL

# Permissions
NONE = hikari.Permissions.NONE
ADMIN = hikari.Permissions.ADMINISTRATOR
