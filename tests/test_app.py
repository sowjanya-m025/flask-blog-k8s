import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as blog  # noqa: E402


class BlogAppTests(unittest.TestCase):
    def setUp(self):
        self.client = blog.app.test_client()
        for pod in blog.PODS.values():
            pod["blogs"].clear()

    def test_home_page_loads(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Pod Alpha", r.data)

    def test_metrics_endpoint_lists_three_pods_and_best_one(self):
        data = self.client.get("/api/metrics").get_json()
        ids = {p["id"] for p in data["pods"]}
        self.assertEqual(ids, {"pod-alpha", "pod-beta", "pod-gamma"})
        self.assertIn(data["best_id"], ids)

    def test_best_pod_has_the_lowest_score(self):
        best, rejected, scored = blog.choose_best_pod()
        self.assertEqual(best["score"], min(p["score"] for p in scored))
        self.assertEqual(len(rejected), 2)

    def test_posting_a_blog_stores_it_on_the_chosen_pod(self):
        r = self.client.post("/", data={"title": "Hello", "content": "World"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(sum(len(p["blogs"]) for p in blog.PODS.values()), 1)
        self.assertIn(b"Hello", r.data)

    def test_empty_post_is_ignored(self):
        self.client.post("/", data={"title": " ", "content": ""})
        self.assertEqual(sum(len(p["blogs"]) for p in blog.PODS.values()), 0)

    def test_user_input_is_html_escaped(self):
        r = self.client.post("/", data={"title": "<script>alert(1)</script>", "content": "x"})
        self.assertNotIn(b"<script>alert(1)</script>", r.data)
        self.assertIn(b"&lt;script&gt;", r.data)

    def test_simulate_load_spikes_a_pod(self):
        r = self.client.post("/api/simulate-load/pod-beta")
        self.assertTrue(r.get_json()["ok"])
        # the background drift thread can move it by up to 20 right after the spike
        self.assertGreaterEqual(blog.PODS["pod-beta"]["cpu"], 55)

    def test_simulate_load_unknown_pod_returns_404(self):
        self.assertEqual(self.client.post("/api/simulate-load/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main()
