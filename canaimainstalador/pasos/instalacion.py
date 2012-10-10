#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ==============================================================================
# PAQUETE: canaima-instalador
# ARCHIVO: canaimainstalador/pasos/instalacion.py
# COPYRIGHT:
#       (C) 2012 William Abrahan Cabrera Reyes <william@linux.es>
#       (C) 2012 Erick Manuel Birbe Salazar <erickcion@gmail.com>
#       (C) 2012 Luis Alejandro Martínez Faneyth <luis@huntingbears.com.ve>
# LICENCIA: GPL-3
# ==============================================================================
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# COPYING file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# CODE IS POETRY

import os, gtk, webkit, sys, threading, shutil, filecmp

from canaimainstalador.clases.particiones import Particiones
from canaimainstalador.clases.common import UserMessage, ProcessGenerator, \
    reconfigurar_paquetes, desinstalar_paquetes, instalar_paquetes, lista_cdroms, \
    crear_etc_default_keyboard, crear_etc_hostname, crear_etc_hosts, \
    crear_etc_network_interfaces, crear_etc_fstab, assisted_mount, \
    assisted_umount, preseed_debconf_values, debug_list, mounted_targets, \
    mounted_parts, crear_usuarios
from canaimainstalador.config import INSTALL_SLIDES

class PasoInstalacion(gtk.Fixed):
    def __init__(self, CFG):
        gtk.Fixed.__init__(self)
        self.p = Particiones()
        self.w = CFG['w']
        self.metodo = CFG['metodo']
        self.acciones = CFG['acciones']
        self.teclado = CFG['teclado']
        self.passroot = CFG['passroot1']
        self.nombre = CFG['nombre']
        self.usuario = CFG['usuario']
        self.passuser = CFG['passuser1']
        self.maquina = CFG['maquina']
        self.oem = CFG['oem']
        self.gdm = CFG['gdm']
        self.mountpoint = '/target'
        self.squashfs = '/live/image/live/filesystem.squashfs'
        self.requesturl = 'http://www.google.com/'
        self.uninstpkgs = ['canaima-instalador']
        self.reconfpkgs = [
            'canaima-estilo-visual-gnome', 'canaima-plymouth',
            'canaima-chat-gnome', 'canaima-bienvenido-gnome',
            'canaima-escritorio-gnome', 'canaima-base'
            ]
        self.instpkgs_burg = [
            ['/live/image/pool/main/libx/libx86', 'libx86-1'],
            ['/live/image/pool/main/s/svgalib', 'libsvga1'],
            ['/live/image/pool/main/libs/libsdl1.2', 'libsdl1.2debian-alsa'],
            ['/live/image/pool/main/libs/libsdl1.2', 'libsdl1.2debian'],
            ['/live/image/pool/main/g/gettext', 'gettext-base'],
            ['/live/image/pool/main/b/burg-themes', 'burg-themes-common'],
            ['/live/image/pool/main/b/burg-themes', 'burg-themes'],
            ['/live/image/pool/main/b/burg', 'burg-common'],
            ['/live/image/pool/main/b/burg', 'burg-emu'],
            ['/live/image/pool/main/b/burg', 'burg-pc'],
            ['/live/image/pool/main/b/burg', 'burg']
            ]
        self.instpkgs_cpp = [[
            '/live/image/pool/main/c/canaima-primeros-pasos/',
            'canaima-primeros-pasos'
            ]]
        self.instpkgs_cagg = [[
            '/live/image/pool/main/c/canaima-accesibilidad-gdm-gnome/',
            'canaima-accesibilidad-gdm-gnome'
            ]]
        self.debconflist = [
            'burg-pc burg/linux_cmdline string quiet splash',
            'burg-pc burg/linux_cmdline_default string quiet splash vga=791',
            'burg-pc burg-pc/install_devices multiselect {0}'.format(self.metodo['disco'][0])
            ]
        self.bindlist = [
            ['/dev', self.mountpoint + '/dev', ''],
            ['/dev/pts', self.mountpoint + '/dev/pts', ''],
            ['/sys', self.mountpoint + '/sys', ''],
            ['/proc', self.mountpoint + '/proc', '']
            ]
        self.connection = True
        self.mountlist = []

        self.visor = webkit.WebView()
        self.visor.set_size_request(700, 430)
        self.visor.open(INSTALL_SLIDES)
        self.put(self.visor, 0, 0)

        self.lblDesc = gtk.Label()
        self.lblDesc.set_size_request(700, 30)
        self.put(self.lblDesc, 0, 440)

        self.w.siguiente.set_label('Reiniciar más tarde')
        self.w.siguiente.set_size_request(150, 30)

        self.w.anterior.set_label('Reiniciar ahora')
        self.w.anterior.set_size_request(150, 30)

        self.w.anterior.hide()
        self.w.siguiente.hide()
        self.w.cancelar.hide()
        self.w.acerca.hide()

#        self.thread = threading.Thread(target=self.instalar, args=())
#        self.thread.start()
        self.instalar()

    def instalar(self):

        if not os.path.isdir(self.mountpoint):
            os.makedirs(self.mountpoint)

        if not os.path.exists(self.squashfs):
            UserMessage(
                message='No se encuentra la imagen squashfs.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if not assisted_umount(
            sync=True, plist=mounted_targets(mnt=self.mountpoint)
            ):
            UserMessage(
                message='Ocurrió un error desmontando las particiones.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if not assisted_umount(
            sync=True, plist=mounted_parts(disk=self.metodo['disco'][0])
            ):
            UserMessage(
                message='Ocurrió un error desmontando las particiones.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Creando particiones en disco ...')
        for a in self.acciones:
            accion = a[0]
            montaje = a[2]
            inicio = a[3]
            fin = a[4]
            fs = a[5]
            tipo = a[6]
            nuevo_fin = a[7]
            disco = self.metodo['disco'][0]
            self.particiones = self.p.lista_particiones(disco)
            self.cdroms = lista_cdroms()

            if accion == 'crear':
                if not self.p.crear_particion(
                    drive=disco, start=inicio, end=fin, fs=fs, partype=tipo
                    ):
                    UserMessage(
                        message='Ocurrió un error creando una partición.',
                        title='ERROR',
                        mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                        c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                        c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                        c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                        )
                else:
                    if montaje:
                        self.mountlist.append([
                            self.p.nombre_particion(disco, tipo, inicio, fin),
                            self.mountpoint + montaje, fs
                            ])

            elif accion == 'borrar':
                particion = self.p.nombre_particion(disco, tipo, inicio, fin)
                if not self.p.borrar_particion(drive=disco, part=particion):
                    UserMessage(
                        message='Ocurrió un error borrando una partición.',
                        title='ERROR',
                        mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                        c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                        c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                        c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                        )

            elif accion == 'redimensionar':
                particion = self.p.nombre_particion(disco, tipo, inicio, fin)
                if not self.p.redimensionar_particion(
                    drive=disco, part=particion, newend=nuevo_fin
                    ):
                    UserMessage(
                        message='Ocurrió un error redimensionando una partición.',
                        title='ERROR',
                        mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                        c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                        c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                        c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                        )

            elif accion == 'formatear':
                particion = self.p.nombre_particion(disco, tipo, inicio, fin)
                if not self.p.formatear_particion(part=particion, fs=fs):
                    UserMessage(
                        message='Ocurrió un error formateando una partición.',
                        title='ERROR',
                        mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                        c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                        c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                        c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                        )

            elif accion == 'usar':
                if montaje:
                    self.mountlist.append([
                        self.p.nombre_particion(disco, tipo, inicio, fin),
                        self.mountpoint + montaje, fs
                        ])

        unset_boot = ''
        for i in self.p.lista_particiones(self.metodo['disco'][0]):
            for flag in i[6]:
                if flag == 'boot':
                    unset_boot = i[0]

        set_boot = ''
        for part, mount, fs in self.mountlist:
            if mount == self.mountpoint + '/':
                set_boot = part
            elif mount == self.mountpoint + '/boot':
                set_boot = part

        if unset_boot:
            if not self.p.remover_bandera(
                drive=self.metodo['disco'][0], part=unset_boot, flag='boot'
                ):
                UserMessage(
                    message='Ocurrió un error montando los sistemas de archivos.',
                    title='ERROR',
                    mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                    c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                    c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                    c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                    )

        if set_boot:
            if not self.p.asignar_bandera(
                drive=self.metodo['disco'][0], part=set_boot, flag='boot'
                ):
                UserMessage(
                    message='Ocurrió un error montando los sistemas de archivos.',
                    title='ERROR',
                    mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                    c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                    c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                    c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                    )

        self.lblDesc.set_text('Montando sistemas de archivos ...')
        if not assisted_mount(sync=True, bind=False, plist=self.mountlist):
            UserMessage(
                message='Ocurrió un error montando los sistemas de archivos.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Copiando archivos en disco ...')
        if ProcessGenerator(
            'unsquashfs -f -n -d {0} {1}'.format(self.mountpoint, self.squashfs)
            ).returncode != 0:
            UserMessage(
                message='Ocurrió un error copiando los archivos al disco.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Montando sistema de archivos ...')
        if not assisted_mount(sync=True, bind=True, plist=self.bindlist):
            UserMessage(
                message='Ocurrió un error montando los sistemas de archivos.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Instalando gestor de arranque ...')
        if not preseed_debconf_values(
            mnt=self.mountpoint, debconflist=self.debconflist
            ):
            UserMessage(
                message='Ocurrió un error presembrando las respuestas debconf.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if not instalar_paquetes(
            mnt=self.mountpoint, dest='/tmp', plist=self.instpkgs_burg
            ):
            UserMessage(
                message='Ocurrió un error instalando un paquete.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if ProcessGenerator(
            'chroot {0} burg-install --force {1}'.format(
                self.mountpoint, self.metodo['disco'][0]
                )
            ).returncode != 0:
            UserMessage(
                message='Ocurrió un error instalando burg.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if ProcessGenerator(
            'chroot {0} update-burg'.format(self.mountpoint)
            ).returncode != 0:
            UserMessage(
                message='Ocurrió un error actualizando burg.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Generando imagen de arranque ...')
        if ProcessGenerator(
            'chroot {0} /usr/sbin/mkinitramfs -o /boot/{1} {2}'.format(
                self.mountpoint, 'initrd.img-' + os.uname()[2], os.uname()[2]
                )
            ).returncode != 0:
            UserMessage(
                message='Ocurrió un error generando la imagen de arranque.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if ProcessGenerator(
            'chroot {0} update-initramfs -u -t'.format(self.mountpoint)
            ).returncode != 0:
            UserMessage(
                message='Ocurrió un error actualizando la imagen de arranque.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Configurando interfaces de red ...')
        if not crear_etc_hostname(
            mnt=self.mountpoint, cfg='/etc/hostname', maq=self.maquina
            ):
            UserMessage(
                message='Ocurrió un error creando el archivo /etc/hostname.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if not crear_etc_hosts(
            mnt=self.mountpoint, cfg='/etc/hosts', maq=self.maquina
            ):
            UserMessage(
                message='Ocurrió un error creando el archivo /etc/hosts.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=sys.exit, p_2=(1,)
                )

        if not crear_etc_network_interfaces(
            mnt=self.mountpoint, cfg='/etc/network/interfaces'
            ):
            UserMessage(
                message='Ocurrió un error creando el archivo /etc/network/interfaces.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Configurando teclado ...')
        if not crear_etc_default_keyboard(
            mnt=self.mountpoint, cfg='/etc/canaima-base/alternatives/keyboard',
            key=self.teclado
            ):
            UserMessage(
                message='Ocurrió un error configurando el teclado.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Configurando particiones, usuarios y grupos ...')
        if not crear_etc_fstab(
            mnt=self.mountpoint, cfg='/etc/fstab',
            mountlist=self.mountlist, cdroms=self.cdroms
            ):
            UserMessage(
                message='Ocurrió un error creando el archivo /etc/fstab.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if not filecmp.cmp('/etc/passwd', '{0}/etc/passwd'.format(self.mountpoint)):
            shutil.copy2('/etc/passwd', '{0}/etc/passwd'.format(self.mountpoint))

        if not filecmp.cmp('/etc/group', '{0}/etc/group'.format(self.mountpoint)):
            shutil.copy2('/etc/group', '{0}/etc/group'.format(self.mountpoint))

        if not filecmp.cmp('/etc/inittab', '{0}/etc/inittab'.format(self.mountpoint)):
            shutil.copy2('/etc/inittab', '{0}/etc/inittab'.format(self.mountpoint))

        f = open('{0}/etc/mtab'.format(self.mountpoint), 'w')
        f.write('')
        f.close()

        if self.oem:
            self.adm_user = 'root'
            self.adm_password = 'root'
            self.nml_user = 'canaima'
            self.nml_password = 'canaima'
            self.nml_name = 'Mantenimiento'

            if not instalar_paquetes(
                mnt=self.mountpoint, dest='/tmp', plist=self.instpkgs_cpp
                ):
                UserMessage(
                    message='Ocurrió un error instalando un paquete.',
                    title='ERROR',
                    mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                    c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                    c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                    c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                    )

        else:
            self.adm_user = 'root'
            self.adm_password = self.passroot
            self.nml_user = self.usuario
            self.nml_password = self.passuser
            self.nml_name = self.nombre

        if self.gdm:
            if not instalar_paquetes(
                mnt=self.mountpoint, dest='/tmp', plist=self.instpkgs_cagg
                ):
                UserMessage(
                    message='Ocurrió un error instalando un paquete.',
                    title='ERROR',
                    mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                    c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                    c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                    c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                    )

        self.lblDesc.set_text('Creando usuarios de sistema ...')
        if not crear_usuarios(
            mnt=self.mountpoint, a_user=self.adm_user, a_pass=self.adm_password,
            n_name=self.nml_name, n_user=self.nml_user, n_pass=self.nml_password
            ):
            UserMessage(
                message='Ocurrió un error reconfigurando un paquete.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Configurando detalles del sistema operativo ...')
        if not reconfigurar_paquetes(mnt=self.mountpoint, plist=self.reconfpkgs):
            UserMessage(
                message='Ocurrió un error reconfigurando un paquete.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Removiendo instalador del sistema de archivos ...')
        if not desinstalar_paquetes(mnt=self.mountpoint, plist=self.uninstpkgs):
            UserMessage(
                message='Ocurrió un error desinstalando un paquete.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Desmontando sistema de archivos ...')
        if not assisted_umount(sync=True, plist=self.bindlist):
            UserMessage(
                message='Ocurrió un error desmontando las particiones.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        if not assisted_umount(sync = True, plist = self.mountlist):
            UserMessage(
                message='Ocurrió un error desmontando las particiones.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=assisted_umount, p_1=(True, self.bindlist),
                c_2=gtk.RESPONSE_OK, f_2=assisted_umount, p_2=(True, self.mountlist),
                c_3=gtk.RESPONSE_OK, f_3=sys.exit, p_3=(1,)
                )

        self.lblDesc.set_text('Ninguna planta fue lastimada en la creación del estilo visual de este instalador.')

        self.visor.hide()
        self.w.anterior.show()
        self.w.siguiente.show()

