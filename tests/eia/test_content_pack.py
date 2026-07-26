from eia_engine.content_pack import content_for, load_modes_catalog


def test_every_mode_has_authored_consumer_copy():
    modes = load_modes_catalog()
    required = {
        "consumer_description",
        "mechanism",
        "distortion",
        "restoration",
        "experiment",
        "when_supported",
        "when_pressured",
    }

    for register, register_modes in modes.items():
        if register == "distortions":
            continue
        for mode in register_modes:
            copy = content_for(register, mode)
            assert required.issubset(copy)
            assert "describes how the" not in copy["mechanism"]
