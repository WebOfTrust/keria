# -*- encoding: utf-8 -*-
"""
Tests for keria.core.keeping module

"""

import warnings

import pytest
from keri.app import habbing

from keria.core.keeping import ExternManager, RemoteKeeper


def test_extern_manager():
    """Test ExternManager incept, rotate, params lifecycle"""
    with habbing.openHby(name="test", temp=True) as hby:
        rb = RemoteKeeper(
            name=hby.name,
            base=hby.base,
            temp=True,
            reopen=True,
            clear=True,
            headDirPath=hby.db.headDirPath,
        )

        mgr = ExternManager(rb=rb)
        pre = "ECtWlHS2Wbx5M2Rg6nm69PCtzwb1veiRNvDpBGF9Z1ec"

        # incept
        mgr.incept(pre)

        # double incept raises
        with pytest.raises(ValueError, match="Already incepted"):
            mgr.incept(pre)

        # rotate succeeds after incept
        mgr.rotate(pre)

        # params returns extern prefix data
        result = mgr.params(pre)
        assert "extern" in result
        assert result["extern"]["algo"] == "extern"
        assert result["extern"]["pidx"] == 0

        # rotate unknown pre raises
        with pytest.raises(ValueError, match="nonexistent or invalid"):
            mgr.rotate("EUnknownPrefix")

        # params unknown pre raises
        with pytest.raises(ValueError, match="nonexistent or invalid"):
            mgr.params("EUnknownPrefix")


def test_extern_keeper_deprecation():
    """Test that importing ExternKeeper emits a DeprecationWarning"""
    import keria.core.keeping as keeping_mod

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        cls = getattr(keeping_mod, "ExternKeeper")
        assert cls is ExternManager
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "ExternManager" in str(w[0].message)


def test_module_getattr_unknown():
    """Test that accessing an unknown attribute raises AttributeError"""
    import keria.core.keeping as keeping_mod

    with pytest.raises(AttributeError, match="has no attribute"):
        getattr(keeping_mod, "NoSuchThing")
