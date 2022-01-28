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

class WorkingPlace(models.Model):
    _name = 'working.place'
    _description = 'Working Place'

    name = fields.Char('Name', size=64, required=True)
    code = fields.Char('Code', size=8, required=True)
    street = fields.Char('Street', size=100)
    number = fields.Char('Number', size=4)
    number_extra = fields.Char('Number Extra', size=4)
    post_code = fields.Char('Postal code', size=12)
    county = fields.Char('County', size=35)
    city = fields.Char('City', size=35)
    work_time = fields.Char('Work time', size=1000)
    spec = fields.Char('Specific', size=1000)
    company_id = fields.Many2one('res.company', 'Company', index=1)
    active = fields.Boolean('Active', default=True)
    fisc_state = fields.Selection([('new', 'New'), ('open', 'Open/In use'), ('closed', 'Closed')], string='Fiscalization state', readonly=True, default='new')

    def activate_wp(self):
        vals_to_write = {}
        vals_to_write['fisc_state'] = 'open'
        vals_to_write['active'] = True

        return self.write(vals_to_write)

    def deactivate_wp(self):
        vals_to_write = {}
        vals_to_write['fisc_state'] = 'closed'
        vals_to_write['active'] = False

        return self.write(vals_to_write)
