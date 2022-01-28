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
from odoo.exceptions import UserError
from signxml import XMLSigner, XMLVerifier, methods
from OpenSSL import crypto
import lxml.etree as ET
import xml
import xml.dom.minidom
import textwrap
import http.client
import base64
import ssl

class Fiscalization(models.Model):
    _name = 'fiscalization.hr'
    _description = "Fiscalization HR"

    def nice_xml(self, xml_msg):
        if not xml_msg:
            return ""
        pretty_xml = xml.dom.minidom.parseString(xml_msg)

        new_xml = ""
        for line in pretty_xml.toprettyxml().split('\n'):
            if len(line.replace('\t','').strip())>0:
                new_xml = new_xml + "\n".join(textwrap.wrap(line,120)) + "\n"

        return new_xml

    def soap_message(self, message):
        res = {}
        try:
            state = 'ok'
            response = self.soap_message_send(message)
            #provjera greske
            if response.find('<tns:Greske>') >= 0 or response.find('<env:Fault>') >= 0:
                state = 'error'
        except Exception as e:
            state = 'wrong'
            response = e


        res['state'] = state
        res['response'] = response
        return res

    def soap_message_send(self, message):
        SM_TEMPLATE = """<soapenv:Envelope
        xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchemainstance">
        <soapenv:Body>
        %s
        </soapenv:Body>
        </soapenv:Envelope>
        """

        company = self.env.user.company_id
        if not company.server_address:
            raise UserError(_('No server address available for current company!'))
        if not company.server_port:
            raise UserError(_('No server port available for current company!'))
        if not company.service_name:
            raise UserError(_('No service name available for current company!'))
        SoapMessage = SM_TEMPLATE%(message)

        server_address = company.server_address + ":" + company.server_port
        service_name = "/" + company.service_name
        webservice = http.client.HTTPSConnection(server_address, timeout=20, context=ssl._create_unverified_context())
        webservice.putrequest("POST", service_name)
        webservice.putheader("Host", company.server_address)
        webservice.putheader("User-Agent", "Python post")
        webservice.putheader("Content-type", "text/xml")
        webservice.putheader("Content-length", "%d" % len(SoapMessage))
        webservice.putheader("SOAPAction", "\"\"")
        webservice.endheaders()
        webservice.send(SoapMessage.encode('utf-8'))
        res = webservice.getresponse().read()
        webservice.close()

        return res.decode('utf-8')

    def _sanitize_cert(self, data):
        data = data.decode('utf-8')
        data = data.replace('-----BEGIN CERTIFICATE-----\n','')
        data = data.replace('-----END CERTIFICATE-----\n','')
        data = data.replace('\n','')
        data.strip()
        data = data.encode('utf-8')
        return data

    def _construct_keyinfo(self, cert, cert_pem):

        KI_template = '''
              <KeyInfo>
              </KeyInfo>
        '''

        keyinfo = ET.fromstring(KI_template)

        cert_crypto = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
        cert_raw = crypto.dump_certificate(crypto.FILETYPE_PEM,cert_crypto)
        cert_serial_int = cert_crypto.get_serial_number()
        cert_serial_text = str(cert_serial_int)

        cert_issuer = cert_crypto.get_issuer()
        cert_issuer_components = cert_issuer.get_components()
        cit = []
        for label in [ 'CN', 'L', 'O', 'C']:
            for comp,val_oid in cert_issuer_components:
                if comp == label:
                    cit.append("{}={}".format(comp,val_oid))

        cert_issuer_text = ', '.join(cit)

        cert_text = self._sanitize_cert(cert_raw)

        x509Data = ET.SubElement(keyinfo, 'X509Data',xmlns="http://www.w3.org/2000/09/xmldsig#")

        X509IssuerSerial = ET.SubElement(x509Data, 'X509IssuerSerial')
        X509IssuerName = ET.SubElement(X509IssuerSerial, 'X509IssuerName')
        X509IssuerName.text = cert_issuer_text
        X509SerialNumber = ET.SubElement(X509IssuerSerial, 'X509SerialNumber')
        X509SerialNumber.text = cert_serial_text

        X509Certificate = ET.SubElement(x509Data, 'X509Certificate')
        X509Certificate.text = cert_text

        #print ET.tostring(keyinfo, encoding='utf-8')
        return keyinfo

    def sign_file(self, msg, uri_id):

        cert = self.env.user.company_id.certificate
        if not cert:
            raise osv.except_osv(_('Error'),_('No certificate available for current company!'))

        cert_decoded = base64.decodestring(cert)

        password = self.env.user.company_id.certificate_pass
        if not password:
            raise osv.except_osv(_('Error'),_('No certificate password available for current company!'))

        process = None
        signed_xml = ''

        cert_64enc = self.env.user.company_id.certificate_pem
        key_64enc = self.env.user.company_id.certificate_key

        if not key_64enc:
            raise ValidationError(_('No certificate key available for current company!'))

        if not cert_64enc:
            raise ValueError(_('No certificate available for current company!'))

        cert_raw = cert

        key = base64.decodestring(key_64enc)
        cert = base64.decodestring(cert_64enc)

        root = ET.fromstring(msg)

        signer = XMLSigner(c14n_algorithm=u'http://www.w3.org/2001/10/xml-exc-c14n#', signature_algorithm="rsa-sha1", digest_algorithm="sha1")

        ns = {}
        ns[None] = signer.namespaces['ds']
        signer.namespaces = ns

        keyinfo = self._construct_keyinfo(cert, cert_raw)

        signed_root = signer.sign(root, key=key, cert=cert, reference_uri=('#%s' % uri_id), key_info=keyinfo)
        signed_xml = ET.tostring(signed_root, encoding='utf-8')
        signed_xml_string = signed_xml.decode('utf-8')
        #print signed_xml

        return signed_xml_string

