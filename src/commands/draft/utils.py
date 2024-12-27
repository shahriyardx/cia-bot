import hikari


async def check_draft_abiliity():
    pass


async def draft_player():
    pass


def get_option_values(i: hikari.CommandInteraction):
    options = {}

    for opt in i.options:
        val = opt.value

        if opt.type == hikari.OptionType.ROLE:
            val = i.resolved.roles[opt.value]

        if opt.type == hikari.OptionType.USER:
            val = i.resolved.members[opt.value]

        if opt.type == hikari.OptionType.CHANNEL:
            val = i.resolved.channels[opt.value]

        if opt.type == hikari.OptionType.ATTACHMENT:
            val = i.resolved.attachments[opt.value].url

        options[opt.name] = val
    print(options)
    return options
