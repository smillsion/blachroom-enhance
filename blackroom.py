# encoding:utf-8

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
import re
from config import conf, global_config


@plugins.register(
    name="blackroom",
    desire_priority=998,
    desc="Being locked in a black room or privilege to somebody",
    version="0.1.1",
    author="dividduang",
    maintainer="david"
)
class Blackroom(Plugin):
    def __init__(self):
        super().__init__()
        self.black_list = []
        self.white_list = []
        config = {}
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.conf = super().load_config()
        self.init_success = True
        if not self.conf:
            logger.warn("[blackroom] inited not found in config")
            self.init_success = False
        else:
            config = self.conf
            logger.info(f"[blackroom] 加载配置文件成功: {config}")
            logger.info("[blackroom] inited")
        if self.init_success:
            self.type = config["type"]
            self.incantation_key = config["incantation"]
            self.amnesty_key = config["amnesty"]
            self.patronus_key = config["patronus"]
            self.ban_key = config["ban"]

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type not in [ContextType.TEXT]:
            return
        context = e_context['context']

        msg: ChatMessage = context['msg']
        isgroup = e_context["context"].get("isgroup")
        nickname = msg.actual_user_nickname  # 获取nickname

        isadmin = self.is_admin_in_group(e_context["context"])
        result = "string"
        ok = False

        if context.content.startswith('$blackroom'):
            if isgroup:
                ok, result = True, f"请勿在群聊中执行该指令"
            elif not isadmin:
                ok, result = True, f"需要管理员权限执行"
            else:
                cmd = context.content.split()
                if len(cmd) == 2 and cmd[1] == "help":
                    ok, result = True, f"查询当前类型：$blackroom type get\n\n修改类型：$blackroom type set white/black"
                if len(cmd) >= 3 and cmd[1] == 'type':
                    if cmd[2] == 'set':
                        if cmd[3] == "white" or cmd[3] == "black":
                            self.type = cmd[3]
                            self.black_list = []
                            self.white_list = []
                            ok, result = True, f"设置成功，当前type为：" + cmd[3]
                        else:
                            ok, result = True, f"type参数错误，white-白名单模式，black-黑名单模式"
                    elif cmd[2] == 'get':
                        ok, result = True, f"当前type为：" + self.type
        elif self.type == "black":
            if nickname in self.black_list:
                logger.warning(f"[WX] {nickname} in In BlackRoom, ignore")
                ok, result = True, f"{self.amnesty_key[1]}"

            # 启动命令
            if self.incantation_key[0] in context.content:
                mmnick = re.findall(r'@(\S+)', context.content)
                at_str = re.findall(r'@', context.content)
                if not at_str:
                    pass
                elif not mmnick:
                    ok, result = True, f"需要@一个用户"
                # 非管理员
                elif not isadmin:
                    ok, result = True, "需要管理员权限执行"
                else:
                    nick = mmnick[0]
                    # 已经在black_list
                    if nickname in self.black_list or nick in self.black_list:
                        ok, result = True, self.incantation_key[1]
                    else:
                        # 添加进已经在black_list
                        self.black_list.append(nick)
                        logger.warning(f"[WX] {nick} {self.incantation_key[2]}")
                        ok, result = True, f"{self.incantation_key[2]}"

            # 解除小黑屋
            elif self.amnesty_key[0] in context.content:
                mmnick = re.findall(r'@(\S+)', context.content)
                at_str = re.findall(r'@', context.content)
                if not at_str:
                    pass
                elif not mmnick:
                    ok, result = True, f"需要@一个用户"
                # 非管理员
                elif not isadmin:
                    ok, result = True, "需要管理员权限执行"
                else:
                    nick = mmnick[0]
                    # 不在小黑屋
                    if nickname not in self.black_list and nick not in self.black_list:
                        ok, result = True, f"{self.amnesty_key[3]}"
                    else:
                        self.black_list.remove(nick)
                        logger.warning(f"[WX] {nick} {self.amnesty_key[2]}")
                        ok, result = True, f"{self.amnesty_key[2]}"
            elif isadmin:
                ok, result = False, f"关键词不命中，管理员跳过权限校验"
        elif self.type == "white":
            if nickname not in self.white_list:
                logger.warning(f"[WX] {nickname} not In WhiteRoom, ignore")
                ok, result = True, f"{self.ban_key[1]}"

            # 启动守护
            if self.patronus_key[0] in context.content:
                mmnick = re.findall(r'@(\S+)', context.content)
                at_str = re.findall(r'@', context.content)
                if not at_str:
                    ok = False
                    pass
                elif not mmnick:
                    ok, result = True, f"需要@一个用户"
                elif not isadmin:
                    ok, result = True, "需要管理员权限执行"
                else:
                    nick = mmnick[0]
                    # 不在white_list
                    if nick not in self.white_list:
                        # 添加进已经在white_list
                        self.white_list.append(nick)
                        ok, result = True, self.patronus_key[2]
                    else:
                        # 在white_list
                        logger.warning(f"[WX] {nick} {self.patronus_key[1]}")
                        ok, result = True, f"{self.patronus_key[1]}"

            # 解除守护
            elif self.ban_key[0] in context.content:
                mmnick = re.findall(r'@(\S+)', context.content)
                at_str = re.findall(r'@', context.content)
                if not at_str:
                    ok = False
                    pass
                elif not mmnick:
                    ok, result = True, f"需要@一个用户"
                elif not isadmin:
                    ok, result = True, "需要管理员权限执行"
                else:
                    nick = mmnick[0]
                    # 在white_list
                    if nick in self.white_list:
                        ok, result = True, f"{self.ban_key[2]}"
                        self.white_list.remove(nick)
                    else:
                        logger.warning(f"[WX] {nick} {self.ban_key[3]}")
                        ok, result = True, f"{self.ban_key[3]}"
            elif isadmin:
                ok, result = False, f"关键词不命中，管理员跳过权限校验"

        reply = Reply()
        if ok:
            reply.type = ReplyType.INFO
            reply.content = result
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
        else:
            reply.type = ReplyType.INFO
            reply.content = result
            e_context["reply"] = reply
            e_context.action = EventAction.CONTINUE  # 事件结束，并跳过处理context的默认逻辑

    def is_admin_in_group(self, context):
        if context["isgroup"]:
            return context.kwargs.get("msg").actual_user_id in global_config["admin_users"]
        else:
            return context.kwargs.get("msg").from_user_id in global_config["admin_users"]


    def get_help_text(self, **kwargs):
        help_text = "对群主不客气会被拉到小黑屋哦！"
        return help_text
