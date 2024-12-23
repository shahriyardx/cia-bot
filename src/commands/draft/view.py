import hikari
import miru


def DraftView(clubs):
    class DraftView(miru.View):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.club_id = None
            self.members = []
            self.cancelled = False

        @miru.user_select(
            placeholder="Select Members to draft", min_values=1, max_values=20
        )
        async def btn(self, ctx: miru.ViewContext, menu: miru.UserSelect):
            self.members = menu.values
            await ctx.interaction.edit_initial_response()

        @miru.text_select(
            placeholder="Select Team",
            options=clubs,
            row=2,
        )
        async def team(self, ctx: miru.ViewContext, menu: miru.TextSelect):
            self.club_id = menu.values
            await ctx.interaction.edit_initial_response()

        @miru.button("Submit", row=3)
        async def submit(self, ctx: miru.ViewContext, btn):

            self.stop()

        @miru.button("Cancel", style=hikari.ButtonStyle.DANGER, row=3)
        async def cancel(self, ctx: miru.ViewContext, btn):
            self.cancelled = True
            self.stop()

    return DraftView
