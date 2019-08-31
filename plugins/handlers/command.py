# SCP-079-HIDE - Hide the real sender
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-HIDE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import share_data
from ..functions.etc import bold, thread, user_mention
from ..functions.filters import test_group
from ..functions.telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)

@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{user_mention(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))

        # Request version update
        for hider in glovar.hiders:
            share_data(
                client=client,
                receivers=[hider],
                action="version",
                action_type="ask",
                data={
                    "admin_id": aid,
                    "message_id": mid
                }
            )

        return True
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return False
