"""Tests for the VCV Library catalog parser and cache.

`_parse_listing_html` is tested against a fixed HTML fixture matching the
real library.vcvrack.com template (captured live 2026-09-05) - no network
calls in tests.
"""

from oscmcp.vcv_library import _parse_listing_html, query_modules, save_modules

_FIXTURE_HTML = """
<div class="row">
  <div class="column">
    <p><strong>2</strong><span> modules found</span></p>
  </div>
</div>
<div class="library-thumbnails">
  <div class="library-thumbnail">
    <div class="library-thumbnail-screenshot"><a href="/MM_ModelV/ModelV"><img src="/screenshots/100/MM_ModelV/ModelV.webp" alt="Mockba Modular Model V"/></a></div>
    <div class="library-thumbnail-info">
      <h4><a class="library-thumbnail-brand" href="/?brand=Mockba%20Modular">Mockba Modular</a> <a href="/MM_ModelV/ModelV">Model V</a>
      </h4>
      <p><a class="button-plus" href="https://vcvrack.com/+" title="Available in VCV+"><img src="/Plus-button.png" height="14"/></a><a class="button button-bundle library-tag" href="/MM_ModelV">Model V<strong class="library-price"> $20</strong></a>
      </p>
      <p>Virtual analog 3-oscillator polysynth
      </p>
      <p><a class="button button-tag library-tag" href="/?tag=Polyphonic">Polyphonic</a><a class="button button-tag library-tag" href="/?tag=Oscillator">Oscillator</a>
      </p>
    </div>
  </div>
  <div class="library-thumbnail">
    <div class="library-thumbnail-screenshot"><a href="/VostokInstruments/Asset"><img src="/screenshots/100/VostokInstruments/Asset.webp" alt="Vostok Instruments Asset"/></a></div>
    <div class="library-thumbnail-info">
      <h4><a class="library-thumbnail-brand" href="/?brand=Vostok%20Instruments">Vostok Instruments</a> <a href="/VostokInstruments/Asset">Asset</a>
      </h4>
      <p>
        <button class="button button-ghost library-add hidden" data-plugin="VostokInstruments" data-module="Asset"><i class="fa-solid fa-plus"></i> Add
        </button>
      </p>
      <p>Bipolar Attenuator &amp; DC Source
      </p>
      <p><a class="button button-tag library-tag" href="/?tag=Attenuator">Attenuator</a><a class="button button-tag library-tag" href="/?tag=Utility">Utility</a>
      </p>
    </div>
  </div>
</div>
"""


def test_parses_total_count():
    _, total = _parse_listing_html(_FIXTURE_HTML)
    assert total == 2


def test_parses_paid_module_with_price_and_plus_flag():
    modules, _ = _parse_listing_html(_FIXTURE_HTML)
    model_v = next(m for m in modules if m.module_slug == "ModelV")
    assert model_v.brand == "Mockba Modular"
    assert model_v.name == "Model V"
    assert model_v.price == "20"
    assert model_v.is_plus is True
    assert model_v.tags == ["Polyphonic", "Oscillator"]
    assert model_v.screenshot_url == "https://library.vcvrack.com/screenshots/100/MM_ModelV/ModelV.webp"


def test_parses_free_module_and_unescapes_html_entities():
    modules, _ = _parse_listing_html(_FIXTURE_HTML)
    asset = next(m for m in modules if m.module_slug == "Asset")
    assert asset.brand == "Vostok Instruments"
    assert asset.price is None
    assert asset.is_plus is False
    assert asset.description == "Bipolar Attenuator & DC Source"


def test_save_and_query_roundtrip(tmp_path, monkeypatch):
    import oscmcp.vcv_library as vcv_library

    monkeypatch.setattr(vcv_library, "DB_PATH", tmp_path / "test_vcv_library.db")

    modules, _ = _parse_listing_html(_FIXTURE_HTML)
    save_modules(modules)

    results, total = query_modules()
    assert total == 2
    assert {r["module_slug"] for r in results} == {"ModelV", "Asset"}

    free_results, free_total = query_modules(license_filter="free")
    assert free_total == 1
    assert free_results[0]["module_slug"] == "Asset"

    brand_results, brand_total = query_modules(brand="Mockba Modular")
    assert brand_total == 1
    assert brand_results[0]["module_slug"] == "ModelV"
