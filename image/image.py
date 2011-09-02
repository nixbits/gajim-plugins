# -*- coding: utf-8 -*-
##
import gtk
import os
import base64
import urllib2

from plugins import GajimPlugin
from plugins.helpers import log_calls
from common.xmpp.protocol import NS_XHTML_IM
from dialogs import ImageChooserDialog, ErrorDialog


class ImagePlugin(GajimPlugin):
    @log_calls('ImagePlugin')
    def init(self):
        self.config_dialog = None  # ImagePluginConfigDialog(self)
        self.controls = []
        self.gui_extension_points = {
            'chat_control_base': (self.connect_with_chat_control,
                self.disconnect_from_chat_control),
            'chat_control_base_update_toolbar': (self.update_button_state,
                None)}

    @log_calls('ImagePlugin')
    def connect_with_chat_control(self, chat_control):
        self.chat_control = chat_control
        control = Base(self, self.chat_control)
        self.controls.append(control)

    @log_calls('ImagePlugin')
    def disconnect_from_chat_control(self, chat_control):
        for control in self.controls:
            control.disconnect_from_chat_control()
        self.controls = []

    @log_calls('ImagePlugin')
    def update_button_state(self, chat_control):
        for base in self.controls:
            if base.chat_control == chat_control:
                is_support_xhtml = chat_control.contact.supports(NS_XHTML_IM)
                base.button.set_sensitive(is_support_xhtml and not \
                    chat_control.gpg_is_active)
                if not is_support_xhtml:
                    text = _('This contact does not support XHTML_IM')
                else:
                    text = _('Send image')
                base.button.set_tooltip_text(text)


class Base(object):
    def __init__(self, plugin, chat_control):
        self.plugin = plugin
        self.chat_control = chat_control
        actions_hbox = chat_control.xml.get_object('actions_hbox')
        self.button = gtk.Button(label=None, stock=None, use_underline=True)
        self.button.set_property('relief', gtk.RELIEF_NONE)
        self.button.set_property('can-focus', False)
        img = gtk.Image()
        img.set_from_stock('gtk-orientation-portrait', gtk.ICON_SIZE_BUTTON)
        self.button.set_image(img)
        self.button.set_tooltip_text('Send image')
        send_button = chat_control.xml.get_object('send_button')
        send_button_pos = actions_hbox.child_get_property(send_button,
            'position')
        actions_hbox.add_with_properties(self.button, 'position',
            send_button_pos - 1, 'expand', False)
        id_ = self.button.connect('clicked', self.on_image_button_clicked)
        chat_control.handlers[id_] = self.button
        self.button.show()

    def on_image_button_clicked(self, widget):
        def on_ok(widget, path_to_file):
            filesize = os.path.getsize(path_to_file)  # in bytes
            invalid_file = False
            msg = ''
            if os.path.isfile(path_to_file):
                stat = os.stat(path_to_file)
                if stat[6] == 0:
                    invalid_file = True
                    msg = _('File is empty')
            else:
                invalid_file = True
                msg = _('File does not exist')
            if filesize < 60000:
                img = urllib2.quote(base64.standard_b64encode(open(
                    path_to_file, "rb").read()), '')
                if len(img) > 60000:
                    invalid_file = True
                    msg = _('File too big')
            else:
                invalid_file = True
                msg = _('File too big')
            if invalid_file:
                ErrorDialog(_('Could not load image'), msg)
                return

            dlg.destroy()
            msg = 'HTML image'
            extension = os.path.splitext(os.path.split(path_to_file)[1])[1] \
                .lower()[1:]
            xhtml = ' <img alt="img" src="data:image/%s;base64,%s"/>' % (
                extension, img)
            self.chat_control.send_message(message=msg, xhtml=xhtml)
            self.chat_control.msg_textview.grab_focus()

        dlg = ImageChooserDialog(on_response_ok=on_ok, on_response_cancel=None)

    def disconnect_from_chat_control(self):
        actions_hbox = self.chat_control.xml.get_object('actions_hbox')
        actions_hbox.remove(self.button)