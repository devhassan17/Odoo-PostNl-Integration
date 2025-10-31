odoo.define('postnl_base.checkout', function (require) {
    'use strict';
    const publicWidget = require('web.public.widget');
    publicWidget.registry.PostNLCheckout = publicWidget.Widget.extend({
        selector: '#postnl-options',
        start() {
            const el = this.$el[0];
            const url = el.dataset.urlOptions;
            return this._rpc({route: url, params: {}}).then(data => {
                const cont = this.$el.find('.postnl-options-container');
                cont.empty();
                data.options.forEach(opt => {
                    const item = $(`
                        <div class="form-check">
                          <input class="form-check-input" type="radio" name="postnl_delivery_option" value="${opt.code}" id="pn_${opt.code}">
                          <label class="form-check-label" for="pn_${opt.code}">${opt.label}</label>
                        </div>`);
                    cont.append(item);
                });
            });
        },
    });
    return publicWidget.registry.PostNLCheckout;
});
