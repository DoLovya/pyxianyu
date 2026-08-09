import unittest


class SmokeTest(unittest.TestCase):
    def test_import(self):
        import pyxianyu

        self.assertTrue(hasattr(pyxianyu, "XianyuClient"))

    def test_submodules(self):
        import pyxianyu.apis
        import pyxianyu.core
        import pyxianyu.xianyu_apis
        import pyxianyu.xianyu_live
        import pyxianyu.message
        import pyxianyu.utils

        self.assertTrue(pyxianyu.apis.AuthApi)
        self.assertTrue(pyxianyu.core.XianyuClient)


if __name__ == "__main__":
    unittest.main()
