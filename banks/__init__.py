# This file is part of Aequora.
#
# Aequora is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Aequora is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Aequora.  If not, see <https://www.gnu.org/licenses/>.
"""Entities package containing domain model classes."""
from .paypal import normalizePayPal, elaborate_paypal
from .postepay import normalizePostePay, elaborate_prepaid_card_postepay
from .unicredit import elaborate_checking_account_unicredit
from .revolut_it import elaborate_checking_account_revolut_it
from .revolut_en import elaborate_checking_account_revolut_en

__all__ = ['normalizePayPal', 'elaborate_paypal', 'normalizePostePay', 
           'elaborate_prepaid_card_postepay', 
           'elaborate_checking_account_unicredit', 
           'elaborate_checking_account_revolut_it', 'elaborate_checking_account_revolut_en']

