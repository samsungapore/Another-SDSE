import translator


def test_search_thread_run_and_del(monkeypatch):
    called = {}

    def fake_get_translation(txt):
        called['txt'] = txt
        return ['ok']

    monkeypatch.setattr(translator, 'get_translation', fake_get_translation)

    t = translator.SearchThread()
    out = []
    t.done.connect(lambda data: out.append(data))

    t.set_jp_text('jp')
    t.run()

    assert called['txt'] == 'jp'
    assert out == [['ok']]

    # cover __del__
    t.__del__()


def test_scrape_stub():
    import scrape

    assert scrape.get_translation('x') is None
