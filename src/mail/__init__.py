# -*- coding: utf-8 -*-
"""
邮件发送模块
"""

import smtplib
import ssl
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import List


class MailSender:
    """邮件发送器"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        sender_name: str = "今日热闻",
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.sender_name = sender_name

    def _send_raw(self, msg: MIMEText, recipients: List[str]) -> dict:
        """
        发送邮件

        Returns:
            {"success": bool, "sent_to": [成功], "failed": {地址: 错误}}
        """
        msg["From"] = formataddr((Header(self.sender_name, "utf-8").encode(), self.sender_email))
        msg["To"] = ", ".join(recipients)

        sent_to = []
        failed = {}

        if self.smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=15) as server:
                server.login(self.sender_email, self.sender_password)
                for recipient in recipients:
                    try:
                        server.sendmail(self.sender_email, [recipient], msg.as_string())
                        sent_to.append(recipient)
                    except Exception as e:
                        failed[recipient] = str(e)
        else:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                for recipient in recipients:
                    try:
                        server.sendmail(self.sender_email, [recipient], msg.as_string())
                        sent_to.append(recipient)
                    except Exception as e:
                        failed[recipient] = str(e)

        return {"success": len(sent_to) > 0, "sent_to": sent_to, "failed": failed}

    def send_html(self, subject: str, html: str, recipients: List[str]) -> dict:
        """
        发送 HTML 邮件

        Args:
            subject: 邮件主题
            html: HTML 内容
            recipients: 收件人列表

        Returns:
            {"success": bool, "sent_to": [...], "failed": {...}}
        """
        msg = MIMEText(html, "html", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        return self._send_raw(msg, recipients)

    def send_text(self, subject: str, text: str, recipients: List[str]) -> dict:
        """
        发送纯文本邮件

        Args:
            subject: 邮件主题
            text: 纯文本内容
            recipients: 收件人列表

        Returns:
            {"success": bool, "sent_to": [...], "failed": {...}}
        """
        msg = MIMEText(text, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        return self._send_raw(msg, recipients)
