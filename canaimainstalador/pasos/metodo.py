#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''Clase que configura las particiones'''
# Autor: William Cabrera
# Fecha: 13/10/2011

# Módulos globales
import gtk, os, threading

# Módulos locales
from canaimainstalador.clases.particiones import Particiones
from canaimainstalador.clases.common import floatify, humanize
from canaimainstalador.clases.barra_particiones import BarraParticiones
from canaimainstalador.config import *

class PasoMetodo(gtk.Fixed):
    def __init__(self, CFG):
        gtk.Fixed.__init__(self)

        self.disco = ''
        self.total = ''
        self.metodo = ''
        self.particion = ''
        self.discos = []
        self.particiones = []
        self.libres = []
        self.metodos = {}
        self.cfg = {}
        self.minimo = ESPACIO_TOTAL
        self.part = Particiones()

        # Listar Discos
        self.discos = self.part.lista_discos()
        print 'Se han encontrado los siguientes discos: {0}'.format(self.discos)

        self.lbl1 = gtk.Label('Seleccione el disco donde desea instalar el sistema:')
        self.lbl1.set_size_request(690, 20)
        self.lbl1.set_alignment(0, 0)
        self.put(self.lbl1, 0, 0)

        self.cmb_discos = gtk.combo_box_new_text()
        for d in self.discos:
            self.cmb_discos.append_text(d)
        self.cmb_discos.set_active(0)
        self.cmb_discos.set_size_request(690, 30)
        self.put(self.cmb_discos, 0, 25)
        self.cmb_discos.connect('changed', self.seleccionar_disco)

        self.barra_part = BarraParticiones(self)
        self.barra_part.set_size_request(690, 100)
        self.put(self.barra_part, 0, 60)

        self.lbl2 = gtk.Label('Seleccione el método de instalación:')
        self.lbl2.set_size_request(690, 20)
        self.lbl2.set_alignment(0, 0)
        self.put(self.lbl2, 0, 165)

        self.cmb_metodo = gtk.combo_box_new_text()
        self.cmb_metodo.set_size_request(690, 30)
        self.put(self.cmb_metodo, 0, 190)
        self.cmb_metodo.connect('changed', self.establecer_metodo)

        self.lbl4 = gtk.Label()
        self.lbl4.set_size_request(690, 90)
        self.lbl4.set_alignment(0, 0)
        self.lbl4.set_line_wrap(True)
        self.put(self.lbl4, 0, 225)

        self.show_all()
        self.seleccionar_disco()

    def seleccionar_disco(self, widget=None):
        self.disco = self.cmb_discos.get_active_text()
        print '{0} seleccionado'.format(self.disco)

        self.particiones = self.part.lista_particiones(self.disco)

        if len(self.particiones) == 0:
            MessageBox(self, self, self.disco)
        else:
            self.total = self.particiones[0][9]
            try:
                self.barra_part.expose()
            except:
                pass

            self.lista_metodos()
            self.establecer_metodo()

    def lista_metodos(self, widget=None):
        '''
            Crea una lista de los metodos de instalación disponibles para la
            partición
        '''
        i = 0
        self.metodos = {}
        self.cmb_metodo.get_model().clear()
        total = self.total
        minimo = self.minimo
        tini = self.particiones[0][1]
        tfin = self.particiones[0][2]
        CFG['w'].siguiente.set_sensitive(True)
        self.cmb_metodo.set_sensitive(True)

        for t in self.particiones:
            ini = t[1]
            fin = t[2]
            if tini > ini: tini = ini
            if tfin < fin: tfin = fin
            if t[5] == 'primary' and t[4] != 'free':
                i += 1

        if total > minimo:
            self.metodos['MANUAL:None:0:0:0'] = 'Instalar editando particiones manualmente'

            if i < 4:
                for p in self.particiones:
                    tam = p[3]
                    libre = p[8]
                    usado = p[7]
                    ini = p[1]
                    fin = p[2]
                    part = p[0]
                    fs = p[4]

                    if fs != 'free' and libre >= minimo:
                        msg = 'Instalar redimensionando {0} para liberar espacio ({1} libres)'
                        met = 'REDIM:{0}:{1}:{2}:{3}'.format(part, ini, fin, usado)
                        self.metodos[met] = msg.format(part, humanize(libre))

                    if fs == 'free' and tam >= minimo:
                        msg = 'Instalar usando espacio libre disponible ({0})'
                        met = 'LIBRE:{0}:{1}:{2}:0'.format(part, ini, fin)
                        self.metodos[met] = msg.format(humanize(tam))

            met = 'TODO:{0}:{1}:{2}:0'.format(self.disco, tini, tfin)
            msg = 'Instalar usando todo el disco ({0})'
            self.metodos[met] = msg.format(humanize(total))

        else:
            self.metodos['NONE:None:0:0:0'] = 'El tamaño del disco no es suficiente'
            CFG['w'].siguiente.set_sensitive(False)
            self.cmb_metodo.set_sensitive(False)

        for l1, l2 in sorted(self.metodos.items()):
            self.cmb_metodo.append_text(l2)
        self.cmb_metodo.set_active(0)

    def establecer_metodo(self, widget=None):
        for c, d in self.metodos.items():
            if d == self.cmb_metodo.get_active_text():
                self.met = c

        self.metodo = self.met.split(':')[0]
        self.particion = self.met.split(':')[1]
        self.ini = floatify(self.met.split(':')[2])
        self.fin = floatify(self.met.split(':')[3])
        self.usado = floatify(self.met.split(':')[4])

        if self.metodo == 'TODO':
            msg = 'Al escoger esta opción el nuevo Sistema Operativo ocupará la totalidad de su disco duro. Tenga en cuenta que se borrarán todos los datos y/o sistemas presentes. Puede aprovechar este momento para realizar un respaldo antes de proseguir con la instalación.'
        elif self.metodo == 'LIBRE':
            msg = 'Esta opción le permitirá instalar el Sistema Operativo en el espacio libre de {0} que se encuentra en su disco duro, conservando los demás datos y/o sistemas que se encuentren en las demás porciones del disco.'.format(humanize(self.fin - self.ini))
        elif self.metodo == 'REDIM':
            msg = 'Esta opción permitirá utilizar el espacio libre presente en la partición {0} para instalar el Sistema Operativo. Se redimensionará la partición para liberar el espacio, manteniendo los datos y/o sistemas presentes'.format(self.particion)
        elif self.metodo == 'MANUAL':
            msg = 'Si escoge esta opción se abrirá el editor de particiones, que le permitirá ajustar las particiones según más le convenga. No le recomendamos que utilice esta opción a menos que sepa lo que está haciendo.'
        elif self.metodo == 'NONE':
            msg = 'El sistema operativo necesita al menos 6GB libres para poder instalar. Seleccione otro disco duro.'
        else:
            pass

        self.lbl4.set_text(msg)

class MessageBox(gtk.MessageDialog):
    def __init__(self, padre, parent, disco):
        self.padre = padre
        self.disco = disco
        msg = "El disco {0} necesita una tabla de particiones para la \
instalación. El tipo de tabla de particiones recomendada es msdos.\n\n \
Si presiona cancelar no podrá usar este disco para realizar la \
instalación.".format(self.disco)
        gtk.MessageDialog.__init__(self, parent, gtk.DIALOG_MODAL | \
                                   gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_INFO, gtk.BUTTONS_OK_CANCEL,
                                   msg)
        self.connect('response', self._handle_clicked)
        self.set_title("Disco {0} sin tabla de particiones".format(self.disco))

        # Contenedor General
        self.cont = gtk.Fixed()
        self.cont.show()
        self.vbox.pack_start(self.cont)

        #Sistema de Archivos
        self.hbox = gtk.HBox()
        self.vbox.pack_start(self.hbox)
        self.lbl = gtk.Label('Tipo de tabla de particiones: ')
        self.lbl.set_alignment(0, 0.5)
        self.lbl.show()
        self.hbox.pack_start(self.lbl, False)
        self.cmb_label = gtk.combo_box_new_text()
        self.cmb_label.set_size_request(100, 30)
        self.hbox.pack_start(self.cmb_label)
        self.cmb_label.append_text('msdos (recomendada)')
        self.cmb_label.append_text('aix')
        self.cmb_label.append_text('amiga')
        self.cmb_label.append_text('bsd')
        self.cmb_label.append_text('dvh')
        self.cmb_label.append_text('gpt')
        self.cmb_label.append_text('mac')
        self.cmb_label.append_text('pc98')
        self.cmb_label.append_text('sun')
        self.cmb_label.append_text('loop')
        self.cmb_label.set_active(0)
        self.cmb_label.show()

        self.show_all()
        #self.run()
        #self.destroy()
    def _handle_clicked(self, *args):
        # -5 = OK
        # -6 = CANCEL
        if args[1] == -5:
            cmd = 'parted {0} mklabel {1}'.format(self.disco,
                      gen.get_active_text(self.cmb_label).split(' ')[0])
            os.system(cmd)
            print cmd
            self.padre.seleccionar_disco()
            self.padre.barra_part.show()
            self.padre.cmb_metodo.show()
            self.padre.lbl_info.show()

        else:
            self.padre.barra_part.hide()
            self.padre.cmb_metodo.hide()
            self.padre.lbl_info.hide()
        self.destroy()

        #self.connect('response', self.handle_clicked)

        #def handle_clicked(self, widget=None):
        #    self.destroy()

