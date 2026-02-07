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
from banks.unicredit import elaborate_checking_account_unicredit
from banks.postepay import elaborate_prepaid_card_postepay
from banks.paypal import elaborate_paypal
from banks.revolut_it import elaborate_checking_account_revolut_it
from banks.revolut_en import elaborate_checking_account_revolut_en