odoo.define('postnl_base.checkout', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.PostNLCheckout = publicWidget.Widget.extend({
        selector: 'body',
        start() {
            const $target = this._findCheckoutContainer();
            if (!$target || !$target.length) {
                return Promise.resolve();
            }
            if ($target.find('#postnl-options').length) {
                return Promise.resolve();
            }
            const $block = $(`
                <div id="postnl-options" class="mt-3" data-url-options="/postnl/options" data-url-pickups="/postnl/pickups">
                    <h5>PostNL delivery options</h5>
                    <div class="postnl-options-container"></div>
                </div>
            `);
            $target.append($block);
            return this._loadOptions($block);
        },

        _findCheckoutContainer() {
            const candidates = [
                '#o_wsale_checkout',
                '#o_wsale_payment',
                '.oe_website_sale .checkout',
                '.oe_website_sale .delivery',
                '#wrapwrap .o_wsale_checkout',
                '#wrapwrap .container'
            ];
            for (const sel of candidates) {
                const $el = $(sel);
                if ($el.length) return $el.first();
            }
            return $();
        },

        _loadOptions($root) {
            const url = $root[0].dataset.urlOptions || '/postnl/options';
            return this._rpc({ route: url, params: {} }).then(data => {
                const $cont = $root.find('.postnl-options-container');
                $cont.empty();
                (data && data.options || []).forEach(opt => {
                    const id = `pn_${opt.code}`;
                    const $item = $(`
                        <div class="form-check my-1">
                          <input class="form-check-input" type="radio" name="postnl_delivery_option" value="${opt.code}" id="${id}">
                          <label class="form-check-label" for="${id}">${opt.label}</label>
                        </div>
                    `);
                    $cont.append($item);
                });
            }).catch(() => {
                // ignore if route not available
            });
        },
    });

    return publicWidget.registry.PostNLCheckout;
});
