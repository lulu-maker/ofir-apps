.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
Croatian fiscalization
======================
This module allows you to setup and use Croatian fiscalisation.

You need to import your certificate, setup your fiscal places, invoice journals, payment types, users and taxes. Invoices are fiscalised during the validation process.

If you validate an invoice that has a invoice journal with fiscal place selected then fiscalisation will take place (depending on the payment type: transaction account payment type is the only one that is notfiscalised).


Installation
============
Depending on: kodmasin fiskpy library (pip install fisk)


Configuration
=============

Import your PFX file and password in company settings (new tab called Fiscalization).

Choose test mode or production mode to activate fiscalization.

Setup your other fiscalization data (vat system, sequence type).

Beneath company setup there is a new menu called fiscalization where you can create and activate your fiscal places.

Setup your account taxes with fiscalization types, percentages and names (if type of tax is Other).

Setup your account journals (choose fiscal place if you want to fiscalize invoices created with this journal).

Setup your sequences for that journals (you have to setup the correct format X/Y/Z).

Fiscalization is done when you confirm your invoices.

You can check your fiscalization data in your invoice in new tab called Fiscalization.

If there is an error during fiscalization you can try to fiscalize your invoice later with Fiscalize button in invoice header which is visible when there was an error during fiscalization process.

You can also try to fiscalize more than one invoice through invoice tree view. Just select your invoices and go to Fiscalize action above your list.


Credits
=======

Contributors
------------

* Milan Tribuson <milan@uvid.hr>
* Dean Đaković Bjelajac <dean@uvid.hr>

Maintainer
----------

.. image:: https://odoo.com.hr/web/image/457
   :alt: Uvid d.o.o.
   :target: https://odoo.com.hr/

This module is maintained by company Uvid d.o.o.

A team of professional developers and IT consultants whose goal is to design, develop and implement great solutions for all your business needs.

https://odoo.com.hr/

https://odoo-dev.com/
