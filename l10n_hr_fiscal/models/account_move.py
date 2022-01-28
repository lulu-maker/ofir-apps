# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source ERP and CRM
#    Author: Uvid d.o.o.
#    Copyright: Uvid d.o.o.
#    web: https://odoo.com.hr/
#    e-mail: info@uvid.hr
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from M2Crypto import BIO, RSA, EVP
from collections import defaultdict
import xml.etree.cElementTree as ET
import base64
import hashlib
import uuid
import time
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    number_zki = fields.Char(string='ZKI Number', size=64, readonly=True, default=False)
    number_jir = fields.Char(string='JIR Number', size=64, readonly=True, default=False)
    number_par = fields.Char(string='Paragon Number', size=64, default=False)
    last_msg_snd = fields.Text(string='Fiscalisation send', readonly=True, default=False)
    last_msg_rcv = fields.Text(string='Fiscalisation reply', readonly=True, default=False)
    fisc_state = fields.Selection([
        ('draft', 'Draft'),
        ('error', 'Error'),
        ('done', 'Done'),
        ], string ='Fiscalization state', readonly=True, index=True, default='draft')
    fisc_user_id = fields.Many2one('res.users', string='Fisc User', readonly=True, default=False)
    fisc_date = fields.Datetime(string='Fisc datetime', readonly=True, default=False)
    working_place_id = fields.Many2one(related='journal_id.working_place_id',string='Working Place', store=True, readonly=True, default=False)
    payment_ids = fields.Many2many('account.payment', 'account_invoice_payment_rel', 'invoice_id', 'payment_id', string="Payments", copy=False, readonly=True)

    def copy(self, default=None):
        self.ensure_one()
        if not default:
            default = {}
        d = {
            'number_zki': False,
            'number_jir': False,
            'number_par': False,
            'last_msg_snd': False,
            'last_msg_rcv': False,
            'fisc_state': 'draft',
            'fisc_user_id': False,
            'fisc_date': False,
        }
        d.update(default)
        return super(AccountMove, self).copy(d)

    def button_draft(self):
        # fisc_state checks
        res = super(AccountMove, self).button_draft()
        for move in self:
            if move.fisc_state == 'done':
                raise UserError(_('You cannot reset to draft fiscalized invoices.'))
        return res

    def do_fiscal(self):

        for invoice in self:

            #fisc only invoices paid in full
            if invoice.payment_state != 'paid':
                continue

            use_fiscal = self.env.user.company_id.use_fiscalization
            if not use_fiscal:
                return True

            # TODO: provjeriti jel ok fiskalizirati dalje..
            # paymentFisc = False
            # for line in invoice.payment_ids:
            #     if line.journal_id.payment_type:
            #         paymentFisc = True

            # if not paymentFisc:
            #     return True

            if invoice.move_type in ('in_invoice','in_refund'):
                return True

            #jel vec fiskaliziran? - problem sa razvezivanjem i pon. placanjem
            if invoice.fisc_state == 'done':
                _logger.warning(u"Nemoguce ponovno fiskalizirati; račun: %s .." %invoice.number)
                return True

            if not invoice.fisc_date:
                self.write({'fisc_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            if not invoice.fisc_user_id:
                self.write({'fisc_user_id': self.env.uid})
            invoice = self.browse(invoice.id)
            if not invoice.working_place_id:
                raise UserError(_('No working place defined in invoice %s!') % (invoice.name_get()[0][1]))
            if not invoice.journal_id.working_place_id:
                raise UserError(_('No working place defined in journal %s!') % (invoice.journal_id.name))
            if not invoice.journal_id.working_place_id.code:
                raise UserError(_('Working place %s has no code!') % (invoice.journal_id.working_place_id.name))
            if not invoice.name:
                raise UserError(_('Invoice has no number/sequence!'))

            company_currency_id = self.env.user.company_id.currency_id.id
            if company_currency_id != invoice.currency_id.id:
                raise UserError(_('You cannot fiscalize an invoice which is in foreign currency! Change the invoice currency or payment method!'))

            shop_fisced = invoice.journal_id.working_place_id.fisc_state == 'open'
            use_fiscal = self.env.user.company_id.use_fiscalization

            _logger.info(u"-FISK- do_fiscal(): fiskaliziram - AI[ %s ]: %s !" % (invoice.id, invoice.name))

            if self.env.user.company_id and use_fiscal:
            # if self.env.user.company_id and use_fiscal and paymentFisc:
                if not shop_fisced:
                    raise UserError(_('Shop %s is not in open state!') % (invoice.journal_id.working_place_id.name))
                cert = self.env.user.company_id.certificate_pem
                if cert:
                    if self.number_zki:
                        zki = self.number_zki
                    else:
                        zki = self.get_zki(invoice, invoice.name, cert)
                        if zki:
                            self.write({'number_zki': zki})
                    jir = self.get_jir(invoice, invoice.name, zki, cert)
                    if jir:
                        self.write({'number_jir': jir})
                    else:
                        message = _("Invoice '%s': fiscalization failed.") % invoice.name
                        _logger.info("-FISK- do_fiscal(): - AI[ %s ]: %s !" % (invoice.id, message))

        return True

    def get_zki(self, invoice, number, cert):
        uir = "%0.2f" % invoice.amount_total
        fiscal_obj = self.env['fiscalization.hr']
        if not invoice.fisc_date:
            raise UserError(_('No date found in invoice!'))
        datVrijRacDT = fields.Datetime.context_timestamp(invoice,invoice.fisc_date)
        datVrij = datVrijRacDT.strftime("%d.%m.%Y %H:%M:%S")
        user = self.env.user
        vat = user.company_id.vat
        if not vat:
            raise UserError(_('No VAT code available for current Company!'))
        oib = vat[2:13]
        try:
            numSplit = number.replace('-','/').split('/')
            bor = numSplit[0].strip()
            opp = numSplit[1].strip()
            onu = numSplit[2].strip()
        except:
            raise UserError(_('Wrong invoice number format!'))
        buffer_tmp = str(oib + datVrij + bor + opp + onu + uir)
        decoded = base64.decodestring(cert)
        bio = BIO.MemoryBuffer(decoded)
        rsa = RSA.load_key_bio(bio)
        key = EVP.PKey()
        key.assign_rsa(rsa)
        key.reset_context(md='sha1')
        key.sign_init()
        buffer_tmp_bytes = buffer_tmp.encode('ascii')
        key.sign_update(buffer_tmp_bytes)
        signature = key.sign_final()
        m = hashlib.md5()
        m.update(signature)
        zki = m.hexdigest()
        return zki

    def get_jir(self, invoice, number, zki, cert):
        self.ensure_one()
        myuuid = uuid.uuid1()
        fiscal_obj = self.env['fiscalization.hr']
        datVrijRacDT = fields.Datetime.context_timestamp(invoice,invoice.fisc_date)
        datVrij = datVrijRacDT.strftime("%d.%m.%YT%H:%M:%S")

        user = self.env.user
        vat = user.company_id.vat
        if not vat:
            raise UserError(_('No VAT code available for current Company!'))
        oibTvrtke = vat[2:13]

        vat_system = user.company_id.vat_system
        if not vat_system:
            raise UserError(_('No VAT system selection available for current Company!'))
        if vat_system == 'yes':
            uSusPDV = "true"
        else:
            uSusPDV = "false"

        if not invoice.fisc_date:
            raise ValidationError(_('No fisc date found in invoice!'))

        # TODO: ovo nije create_date, nego datum/vrijeme izdavanja racuna kupcu.. Provjeriti u fisk. teh. spec. !!
        datVrijRacDT = fields.Datetime.context_timestamp(invoice,invoice.create_date)
        datVrijRacun = datVrijRacDT.strftime("%d.%m.%YT%H:%M:%S")
        oznSlijed = user.company_id.count_system
        if not number:
            raise ValidationError(_('No number/sequence found in invoice!'))
        try:
            numSplit = number.replace('-','/').split('/')
            bor = numSplit[0].strip()
            opp = numSplit[1].strip()
            onu = numSplit[2].strip()
        except:
            raise ValidationError(_('Wrong invoice number format!'))

        rootEl = ET.Element("tns:RacunZahtjev")
        rootEl.set("Id", "RacunZahtjev")
        rootEl.set("xmlns:tns", "http://www.apis-it.hr/fin/2012/types/f73")
        rootEl.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

        zagEl = ET.SubElement(rootEl, "tns:Zaglavlje")
        idPorEl = ET.SubElement(zagEl, "tns:IdPoruke")
        idPorEl.text = str(myuuid)
        datumVrijemeEl = ET.SubElement(zagEl, "tns:DatumVrijeme")
        datumVrijemeEl.text = datVrij

        racunEl = ET.SubElement(rootEl, "tns:Racun")
        oibEl = ET.SubElement(racunEl, "tns:Oib")
        oibEl.text = oibTvrtke
        uSusPDVEl = ET.SubElement(racunEl, "tns:USustPdv")
        uSusPDVEl.text = uSusPDV
        datVrijRacunEl = ET.SubElement(racunEl, "tns:DatVrijeme")
        datVrijRacunEl.text = datVrijRacun
        oznSlijedEl = ET.SubElement(racunEl, "tns:OznSlijed")
        oznSlijedEl.text = oznSlijed

        brRacEl = ET.SubElement(racunEl, "tns:BrRac")
        brOznRacEl = ET.SubElement(brRacEl, "tns:BrOznRac")
        brOznRacEl.text = bor
        oznPosPrEl = ET.SubElement(brRacEl, "tns:OznPosPr")
        oznPosPrEl.text = opp
        oznNapUrEl = ET.SubElement(brRacEl, "tns:OznNapUr")
        oznNapUrEl.text = onu

        #porezi
        account_tax_obj = self.env['account.tax']
        pdvEl = ET.SubElement(racunEl, "tns:Pdv")
        pnpEl = ET.SubElement(racunEl, "tns:Pnp")
        foundPDV = 0
        foundPNP = 0
        foundOstali = 0
        ostaliPorEl =ET.SubElement(racunEl, "tns:OstaliPor")

        #[('PDV 25%', 338.25, 1353.0, '338,25 kn', '1.353,00 kn', 1, 4)]
        d_taxes = {}
        d_taxes_grouped = defaultdict(lambda: defaultdict(list))
        for taxes in invoice.invoice_line_ids.tax_ids:
            stopa = taxes.amount
            naziv = taxes.name
            tip = taxes.tax_type
            p_grupa = taxes.tax_group_id.id
            d_taxes.update({p_grupa:(naziv, tip, stopa)})

        for tax_group in invoice.amount_by_group:
            iznos = tax_group[1]
            osnovica = tax_group[2]
            p_grupa = tax_group[6]
            d_taxes_grouped[stopa][tip].append(naziv)
            d_taxes_grouped[stopa][tip].append(iznos)
            d_taxes_grouped[stopa][tip].append(osnovica)

        foundTax = 0
        for stopa in d_taxes_grouped:
            for tip in d_taxes_grouped[stopa]:
                if tip == 'pdv':
                    porezEl = ET.SubElement(pdvEl, "tns:Porez")
                    foundTax = 1
                    foundPDV = 1
                if tip == 'pp':
                    porezEl = ET.SubElement(pnpEl, "tns:Porez")
                    foundTax = 1
                    foundPNP = 1

                if foundTax == 0:
                    porezEl = ET.SubElement(ostaliPorEl, "tns:Porez")
                    porNazivEl = ET.SubElement(porezEl, "tns:Naziv")
                    porNazivEl.text = d_taxes_grouped[stopa][tip][0]
                    foundOstali = 1

                stopaEl = ET.SubElement(porezEl, "tns:Stopa")
                stopaEl.text = "%.2f" % stopa
                osnovicaEl = ET.SubElement(porezEl, "tns:Osnovica")
                osnovicaEl.text = "%.2f" % d_taxes_grouped[stopa][tip][2]
                iznosEl = ET.SubElement(porezEl, "tns:Iznos")
                iznosEl.text = "%.2f" % d_taxes_grouped[stopa][tip][1]

        if foundPDV == 0:
            racunEl.remove(pdvEl)
        if foundPNP == 0:
            racunEl.remove(pnpEl)
        if foundOstali == 0:
            racunEl.remove(ostaliPorEl)

        #TODO
        #iznosOslobPdvEl = ET.SubElement(racunEl, "tns:IznosOslobPdv")
        #iznosOslobPdvEl.text = "0.00"
        #iznosMarzaEl = ET.SubElement(racunEl, "tns:IznosMarza")
        #iznosMarzaEl.text = "0.00"

        #povratna = 0
        #for line in invoice.invoice_line:
        #    if line.product_id and line.product_id.packaging_fee != 0:
        #        povratna = povratna + line.product_id.packaging_fee * line.quantity

        # if povratna > 0:
        #     nakMainEl = ET.SubElement(racunEl, "tns:Naknade")
        #     nakSubEl = ET.SubElement(nakMainEl, "tns:Naknada")
        #     nakPovNazEl = ET.SubElement(nakSubEl, "tns:NazivN")
        #     nakPovNazEl.text = "Povratna naknada"
        #     nakPovIznEl = ET.SubElement(nakSubEl, "tns:IznosN")
        #     nakPovIznEl.text = "%.2f" % povratna
        #END TODO

        iznosUkupnoEl = ET.SubElement(racunEl, "tns:IznosUkupno")
        iznosUkupnoEl.text = "%.2f" % invoice.amount_total

        nacinPl = ""
        # TODO: nacini placanja? stari problem sa wizardom i stavkama placanja
        # for line in invoice.payment_ids:
        #     if not line.journal_id.payment_type:
        #         nacinPl = "O"
        #     if nacinPl != "" and nacinPl != line.journal_id.payment_type:
        #         nacinPl = "O"
        #     if nacinPl == "":
        #         nacinPl = line.journal_id.payment_type
        nacinPl = "G"
        nacinPlacEl = ET.SubElement(racunEl, "tns:NacinPlac")
        nacinPlacEl.text = nacinPl

        oibOperEl = ET.SubElement(racunEl, "tns:OibOper")
        if not invoice.fisc_user_id:
            raise UserError(_('No user found in invoice!'))
        if not invoice.fisc_user_id.vat:
            raise UserError(_('No VAT number for user %s!')%(invoice.fisc_user_id.name))
        oibText = invoice.fisc_user_id.vat
        if not oibText:
            raise UserError(_('No VAT number found for user %s!')%invoice.fisc_user_id.name)
        oibOperEl.text = oibText[2:13]
        zastKodEl = ET.SubElement(racunEl, "tns:ZastKod")
        zastKodEl.text = zki
        nakDostEl = ET.SubElement(racunEl, "tns:NakDost")
        if invoice.fisc_state == 'error' or invoice.number_par:
            nakDostEl.text = "true"
        else:
            nakDostEl.text = "false"

        if invoice.number_par:
            nakDostEl = ET.SubElement(racunEl, "tns:ParagonBrRac")
            nakDostEl.text = invoice.number_par

        msg = ET.tostring(rootEl)

        signed_xml = fiscal_obj.sign_file(msg, 'RacunZahtjev')
        retMsg = fiscal_obj.soap_message(signed_xml)
        snd_xml = fiscal_obj.nice_xml(signed_xml)
        rcv_xml = retMsg['response']

        vals_to_write = {}
        jir_number = False
        if retMsg['state'] == 'ok':
            rcv_xml = fiscal_obj.nice_xml(rcv_xml)
            start_jir = rcv_xml.find('<tns:Jir>')
            end_jir = rcv_xml.find('</tns:Jir>')
            if start_jir>0 and end_jir>0:
                start_jir = start_jir+10
                jir_number = rcv_xml[start_jir:end_jir].strip()
                vals_to_write['fisc_state'] = 'done'
            else:
                vals_to_write['fisc_state'] = 'error'
        else:
            vals_to_write['fisc_state'] = 'error'

        if retMsg['state'] == 'error':
            rcv_xml = fiscal_obj.nice_xml(rcv_xml)

        vals_to_write['last_msg_rcv'] = rcv_xml
        vals_to_write['last_msg_snd'] = snd_xml

        invoice.write(vals_to_write)
        return jir_number
