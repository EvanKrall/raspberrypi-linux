#include <linux/i2c.h>
#include <linux/regmap.h>
#include <linux/gpio/consumer.h>


static const struct i2c_device_id tps61177a_idtable[] = {
      { "tps61177a", 0 },
      { },
};

struct tps61177a {
    struct device *dev;
    struct regmap *regmap;
    struct gpio_desc		*enable_gpio;
};

static const struct regmap_range tps61177a_readable_ranges[] = {
	regmap_reg_range(0xA0, 0xA5),
};

static const struct regmap_range tps61177a_writable_ranges[] = {
	regmap_reg_range(0xA0, 0xA5),
};

static const struct regmap_access_table tps61177a_readable_table = {
	.yes_ranges = tps61177a_readable_ranges,
	.n_yes_ranges = ARRAY_SIZE(tps61177a_readable_ranges),
};

static const struct regmap_access_table tps61177a_writable_table = {
	.yes_ranges = tps61177a_writable_ranges,
	.n_yes_ranges = ARRAY_SIZE(tps61177a_writable_ranges),
};

static const struct regmap_config tps61177a_regmap_config = {
    .reg_bits = 8,
    .val_bits = 8,
    .rd_table = &tps61177a_readable_table,
    .wr_table = &tps61177a_writable_table,
};

static int tps61177a_probe(struct i2c_client *client) {
    struct device *dev = &client->dev;
    struct tps61177a *ctx;
    int ret;

    ctx = devm_kzalloc(dev, sizeof(*ctx), GFP_KERNEL);
    if (!ctx)
        return -ENOMEM;
    ctx->dev = dev;
	ctx->regmap = devm_regmap_init_i2c(client, &tps61177a_regmap_config);
	if (IS_ERR(ctx->regmap)) {
		ret = PTR_ERR(ctx->regmap);
		return ret;
	}

    ctx->enable_gpio = devm_gpiod_get_optional(ctx->dev, "enable",
						   GPIOD_OUT_HIGH);
	if (IS_ERR(ctx->enable_gpio))
		return PTR_ERR(ctx->enable_gpio);

    dev_set_drvdata(dev, ctx);
	i2c_set_clientdata(client, ctx);

    pr_warn("Setting V_UVLO to 3.0V; client %p", client);
    pr_warn("addr %x", client->addr);
    regmap_write(ctx->regmap, 0xa2, 0x02); // Set V_UVLO to 3.0V
    pr_warn("should've written the thing to the stuff");

    return 0;
}

MODULE_DEVICE_TABLE(i2c, tps61177a_idtable);

static const struct of_device_id tps61177a_of_match[] = {
    { .compatible = "ti,tps61177a" },
    { },
};

static struct i2c_driver tps61177a_driver = {
      .driver = {
              .name   = "tps61177a",
              .of_match_table = tps61177a_of_match,
      },

      .id_table       = tps61177a_idtable,
      .probe_new      = tps61177a_probe,

};

module_i2c_driver(tps61177a_driver);


/* Substitute your own name and email address */
MODULE_AUTHOR("Evan Krall <meatmanek@gmail.com>");
MODULE_DESCRIPTION("Driver for TI tps61177a backlight controllers");

/* a few non-GPL license types are also allowed */
MODULE_LICENSE("GPL");