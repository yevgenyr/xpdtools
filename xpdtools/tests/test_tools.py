##############################################################################
#
# xpdan            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Christopher J. Wright
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import pytest

import numpy as np
from numpy.testing import assert_equal

from xpdtools.tests.utils import pyFAI_calib
from xpdtools.tools import (
    load_geo,
    map_to_binner,
    mask_img,
    binned_outlier,
    z_score_image,
    polarization_correction,
    overlay_mask,
    generate_map_bin,
    generate_binner,
    move_center,
)
from xpdtools.jit_tools import mask_ring_median, mask_ring_mean

geo = load_geo(pyFAI_calib)


def test_mask_ring_mean():
    values = np.asarray([0, 0, 0, 10, 0, 0, 0, 0])
    positions = np.arange(0, len(values))
    assert mask_ring_mean(values, positions, 1) == np.argmax(values)


def test_mask_ring_median():
    values = np.asarray([0, 0, 0, 1, 0, 0, 0, 0])
    positions = np.arange(0, len(values))
    assert mask_ring_median(values, positions, 3) == np.argmax(values)


def test_load_geo():
    geo = load_geo(pyFAI_calib)
    assert geo


def test_generate_binner():
    a = generate_binner(geo, (2048, 2048))
    b = map_to_binner(*generate_map_bin(geo, (2048, 2048)))
    assert a
    assert b
    assert_equal(a.flatcount, b.flatcount)


def test_generate_binner_mask():
    b = map_to_binner(
        *generate_map_bin(geo, (2048, 2048)),
        np.random.randint(0, 2, 2048 * 2048, dtype=bool).reshape((2048, 2048))
    )
    assert b


@pytest.mark.parametrize("mask_method", ["mean", "median"])
def test_binned_outlier(mask_method):
    b = map_to_binner(*generate_map_bin(geo, (2048, 2048)))
    img = np.ones((2048, 2048))
    bad = np.unique(np.random.randint(0, 2048 * 2048, 1000))
    urbad = np.unravel_index(bad, (2048, 2048))
    img[urbad] = 100
    mask = binned_outlier(img, b, mask_method=mask_method)

    assert_equal(np.where(mask.ravel() == 0)[0], bad)


def test_z_score_image():
    b = map_to_binner(*generate_map_bin(geo, (2048, 2048)))
    img = np.ones((2048, 2048))
    bad = np.unique(np.random.randint(0, 2048 * 2048, 1000))
    urbad = np.unravel_index(bad, (2048, 2048))
    img[urbad] = 10

    z_score = z_score_image(img, b)
    assert all(z_score[urbad] > 2)


def test_polarization_correction():
    img = np.ones((2048, 2048))
    pimg = polarization_correction(img, geo, .99)
    assert_equal(img / geo.polarization(img.shape, .99), pimg)


def test_overlay_mask():
    img = np.ones(100)
    mask = np.random.randint(0, 2, 100, dtype=bool)
    img2 = overlay_mask(img, mask)
    img[~mask] = np.nan
    assert img2 is not img
    assert_equal(img2, img)


@pytest.mark.parametrize("mask_method", ["mean", "median"])
def test_mask_img(mask_method):
    b = map_to_binner(*generate_map_bin(geo, (2048, 2048)))
    img = np.ones((2048, 2048))
    r = np.random.RandomState(42)
    bad = np.unique(r.randint(0, 2048 * 2048, 1000))
    urbad = np.unravel_index(bad, (2048, 2048))
    img[urbad] = 10
    mask = mask_img(
        img,
        b,
        auto_type=mask_method,
        edge=None,
        lower_thresh=None,
        upper_thresh=None,
    )

    assert_equal(np.where(mask.ravel() == 0)[0], bad)


def test_move_center():
    m = (.1, .1)
    g2 = move_center(m, geo)
    nn = ("poni1", "poni2")
    for mm, n in zip(m, nn):
        assert getattr(g2, n) == getattr(geo, n) + mm
