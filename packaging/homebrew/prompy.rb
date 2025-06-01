class Prompy < Formula
  include Language::Python::Virtualenv

  desc "Command-line tool for building and managing reusable prompt templates for AI tools"
  homepage "https://github.com/jhugman/prompy"
  url "https://files.pythonhosted.org/packages/source/p/prompy/prompy-0.1.0.tar.gz"
  sha256 "01e9555be8b329935011e6927889841a9373bf08cbafc7bb7968f863fa8dda5b"
  license "MIT"

  depends_on "python@3.9"

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.2.0.tar.gz"
    sha256 "fdb9b2fa8985b2db1a1c970b893ee3b5932e5a0e91d0d33b93e0b5b6b4acc653"
  end

  resource "jinja2" do
    url "https://files.pythonhosted.org/packages/source/j/jinja2/jinja2-3.1.6.tar.gz"
    sha256 "eb93e86a1a85b3d8ba1a42d7e0f86b3f3b4c1cbca8b42a1fd5c2ee1a0b8a7aa8"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/pyyaml-6.0.2.tar.gz"
    sha256 "d584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e"
  end

  resource "pyperclip" do
    url "https://files.pythonhosted.org/packages/source/p/pyperclip/pyperclip-1.9.0.tar.gz"
    sha256 "b7de0142ddc81bfc5c7507eea19da920b92252b548b96186caf94a5e2527d310"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-14.0.0.tar.gz"
    sha256 "8260cda28e3db6bf04d2d1ef4dbc03ba80a824c88b0e7668a0f23126a424844a"
  end

  resource "markupsafe" do
    url "https://files.pythonhosted.org/packages/source/m/markupsafe/markupsafe-3.0.2.tar.gz"
    sha256 "ee55d3edf80167e48ea11a923c7386f4669df67d7994554387f84e7d8b0a2bf0"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    # Test that the command runs and shows help
    assert_match "Usage: prompy", shell_output("#{bin}/prompy --help")

    # Test that we can get version info
    assert_match "prompy, version 0.1.0", shell_output("#{bin}/prompy --version")

    # Test basic functionality by creating a config dir and running list
    testpath_config = testpath/".config/prompy"
    testpath_config.mkpath
    ENV["PROMPY_CONFIG_DIR"] = testpath_config
    shell_output("#{bin}/prompy list")
  end
end
