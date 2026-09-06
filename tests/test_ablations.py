import unittest

from predictive_pc_fmcw.ablations import paper_ablation_specs


class PaperAblationDesignTest(unittest.TestCase):
    def test_ablation_names_are_unique(self):
        specs = paper_ablation_specs()
        names = [spec.name for spec in specs]
        self.assertEqual(len(names), len(set(names)))

    def test_zero_lifetime_alias_is_not_a_separate_ablation(self):
        specs = {spec.name: spec for spec in paper_ablation_specs()}
        self.assertNotIn("no_link_lifetime_urgency", specs)
        self.assertEqual(specs["trajectory_predictive"].scheduler, "predictive_utility")
        self.assertEqual(specs["link_lifetime"].scheduler, "link_lifetime")

    def test_full_channel_is_only_the_declared_channel_reference_alias(self):
        specs = {spec.name: spec for spec in paper_ablation_specs()}
        full = specs["full_channel"]
        reference = specs["link_lifetime"]
        self.assertEqual(full.scheduler, reference.scheduler)
        self.assertEqual(full.channel_mode, "full")
        self.assertEqual(reference.channel_mode, "full")


if __name__ == "__main__":
    unittest.main()
