"""
Sphinx extension for viewing feature toggle annotations.
"""
import os

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from code_annotations.contrib.config import FEATURE_TOGGLE_ANNOTATIONS_CONFIG_PATH

from .base import find_annotations, quote_value


def find_feature_toggles(source_path):
    """
    Find the feature toggles as defined in the configuration file.

    Return:
        toggles (dict): feature toggles indexed by name.
    """
    return find_annotations(
        source_path, FEATURE_TOGGLE_ANNOTATIONS_CONFIG_PATH, ".. toggle_name:"
    )


class FeatureToggles(SphinxDirective):
    """
    Sphinx directive to list the feature toggles in a single documentation page.

    Use this directive as follows::

        .. featuretoggles::

    This directive supports the following configuration parameters:

    - ``featuretoggles_source_path``: absolute path to the repository file tree. E.g:

        featuretoggles_source_path = os.path.join(os.path.dirname(__file__), "..", "..")

    - ``featuretoggles_repo_url``: Github repository where the code is hosted. E.g:

        featuretoggles_repo_url = "https://github.com/openedx/myrepo"

    - ``featuretoggles_repo_version``: current version of the git repository. E.g:

        import git
        try:
            repo = git.Repo(search_parent_directories=True)
            featuretoggles_repo_version = repo.head.object.hexsha
        except git.InvalidGitRepositoryError:
            featuretoggles_repo_version = "master"
    """

    required_arguments = 0
    optional_arguments = 0
    option_spec = {}

    def run(self):
        """
        Public interface of the Directive class.

        Return:
            nodes (list): nodes to be appended to the resulting document.
        """
        return list(self.iter_nodes())

    def iter_nodes(self):
        """
        Iterate on the docutils nodes generated by this directive.
        """
        toggles = find_feature_toggles(self.env.config.featuretoggles_source_path)
        for toggle_name in sorted(toggles):
            toggle = toggles[toggle_name]
            toggle_default_value = toggle.get(".. toggle_default:", "Not defined")
            toggle_default_node = nodes.literal(text=quote_value(toggle_default_value))
            toggle_section = nodes.section("", ids=[f"featuretoggle-{toggle_name}"])
            toggle_section += nodes.title(text=toggle_name, ids=[f"name-{toggle_name}"])
            toggle_section += nodes.paragraph(
                "", "Default: ", toggle_default_node, ids=[f"default-{toggle_name}"]
            )
            toggle_section += nodes.paragraph(
                "",
                "Source: ",
                nodes.reference(
                    text="{} (line {})".format(
                        toggle["filename"], toggle["line_number"]
                    ),
                    refuri="{}/blob/{}/{}#L{}".format(
                        self.env.config.featuretoggles_repo_url,
                        self.env.config.featuretoggles_repo_version,
                        toggle["filename"],
                        toggle["line_number"],
                    ),
                ),
                ids=[f"source-{toggle_name}"],
            )
            toggle_section += nodes.paragraph(
                text=f'Desc: {toggle.get(".. toggle_description:", "NaN")}',
                ids=[f"description-{toggle_name}"],
            )
            if toggle.get(".. toggle_warning:") not in (None, "None", "n/a", "N/A"):
                toggle_section += nodes.warning(
                    "", nodes.paragraph("", toggle[".. toggle_warning:"]), ids=[f"warning-{toggle_name}"]
                )
            optional_attrs = [
                "creation_date",
                "target_removal_date",
                "implementation",
                "use_cases",
            ]
            for opt in optional_attrs:
                if toggle.get(f".. toggle_{opt}:") not in (None, "None", "n/a", "N/A"):
                    toggle_section += nodes.paragraph(
                        text=f'{opt.title().replace("_"," ")}: {toggle[f".. toggle_{opt}:"]}',
                        ids=[f"{opt}-{toggle_name}"],
                    )
            yield toggle_section


def setup(app):
    """
    Declare the Sphinx extension.
    """
    app.add_config_value(
        "featuretoggles_source_path",
        os.path.abspath(".."),
        "env",
    )
    app.add_config_value("featuretoggles_repo_url", "", "env")
    app.add_config_value("featuretoggles_repo_version", "master", "env")
    app.add_directive("featuretoggles", FeatureToggles)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
