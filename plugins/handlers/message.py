# SCP-079-HIDE - Hide the real sender
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
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
from ..functions.channel import exchange_to_hide
from ..functions.etc import code, general_link, lang, thread
from ..functions.filters import aio, exchange_channel, hide_channel
from ..functions.receive import receive_help_send, receive_text_data
from ..functions.telegram import forward_messages, send_message

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.channel & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & hide_channel, group=-1)
def exchange_emergency(client: Client, message: Message) -> bool:
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        if "EMERGENCY" not in receivers:
            return True

        if action != "backup":
            return True

        if action_type != "hide":
            return True

        if data is True:
            glovar.should_hide = data
        elif data is False and sender == "MANAGE":
            glovar.should_hide = data

        project_text = general_link(glovar.project_name, glovar.project_link)
        hide_text = (lambda x: lang("enabled") if x else "disabled")(glovar.should_hide)
        text = (f"{lang('project')}{lang('colon')}{project_text}\n"
                f"{lang('action')}{lang('colon')}{code(lang('transfer_channel'))}\n"
                f"{lang('emergency_channel')}{lang('colon')}{code(hide_text)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & exchange_channel)
def forward_others_data(client: Client, message: Message) -> bool:
    # Forward message from other bots to hiders
    result = False

    glovar.locks["receive"].acquire()

    try:
        if glovar.should_hide:
            return False

        data = receive_text_data(message)

        if not data:
            return False

        sender = data["from"]
        receivers = data["to"]

        if not (any(hider in receivers for hider in glovar.hiders)
                or (sender == "CAPTCHA" and receivers == ["USER"])):
            return False

        cid = glovar.hide_channel_id
        fid = message.chat.id
        mid = message.message_id
        thread(forward_messages, (client, cid, fid, [mid], True))

        result = True
    except Exception as e:
        logger.warning(f"Forward others data error: {e}", exc_info=True)
    finally:
        glovar.locks["receive"].release()

    return result


@Client.on_message((Filters.incoming | aio) & Filters.channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & hide_channel)
def forward_hiders_data(client: Client, message: Message) -> bool:
    # Forward message from hiders to other bots
    result = False

    glovar.locks["receive"].acquire()

    try:
        data = receive_text_data(message)

        if not data:
            return False

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        if sender not in glovar.hiders:
            return False

        # Help hiders
        if glovar.sender in receivers:

            if action == "help":
                if action_type == "send":
                    receive_help_send(client, message, data)

            return True

        # Forward regular exchange text
        if message.outgoing:
            return False

        if glovar.should_hide:
            return False

        cid = glovar.exchange_channel_id
        fid = message.chat.id
        mid = message.message_id

        if forward_messages(client, cid, fid, [mid], True) is not False:
            return True

        exchange_to_hide(client)

        result = True
    except Exception as e:
        logger.warning(f"Forward hiders data error: {e}", exc_info=True)
    finally:
        glovar.locks["receive"].release()

    return result
