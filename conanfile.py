import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.files import replace_in_file, rm
from conan.tools.gnu import MakeDeps
from conan.tools.scm.git import Git

class SplinterDb(ConanFile):
    name = "splinterdb"
    version = "1.0.0"
    settings = "os", "arch", "compiler", "build_type"

    requires = [
        #----- --- -- -  -  -   -
        # We can't use Conan Center's libaio because it is broken when using lto;
        #  install the system package (e.g., apt get libaio-dev)
        #
        # "libaio/[>=0.3]",
        #----- --- -- -  -  -   -
        "libconfig/[>=1.7]",
        "xxhash/[>=0.8]",
    ]

    def layout(self):
        self.folders.build = os.path.join("build", str(self.settings.build_type))
        self.folders.source = os.path.join("splinterdb")
        self.folders.generators = os.path.join(self.folders.build, "generators")
        self.cpp.package.libs = ["splinterdb"]

    def generate(self):
        pc = MakeDeps(self)
        pc.generate()

    def source(self):
        print(f"cwd={os.getcwd()}")
        git = Git(self)
        #git.clone(url="https://github.com/vmware/splinterdb", target=".")

    def build(self):
        run_tests = ""
        if not self.conf.get("user.build:skip_run_tests", default=False):
            run_tests = "run-tests"

        self.run(command=self._splinterdb_make_command(["all", run_tests]),
                 cwd=self.source_folder)

    def package(self):
        self.run(command=self._splinterdb_make_command(["install"]),
                 cwd=self.source_folder)

    def package_info(self):
        self.cpp_info.libs = ["splinterdb"]

    #==#==========+==+=+=++=+++++++++++-+-+--+----- --- -- -  -  -   -

    def _splinterdb_make_command(self, targets):
        splinter_build_modes = {
            "Debug": "debug",
            "Release": "release",
            "RelWithDebInfo": "optimized-debug",
        }

        build_mode = splinter_build_modes[str(self.settings.build_type)]

        vars = (
            f"BUILD_MODE={build_mode} "
            f"BUILD_ROOT={self.build_folder} "
            f"INSTALL_PATH={self.package_folder} "
            f"LD='$(CC)' "
            f"CONAN_INCLUDE_DIR_FLAG=-I "
            f"CONAN_DEFINE_FLAG=-D "
            f"CONAN_LIB_DIR_FLAG=-L "
            f"CFLAGS='-Dalignof=_Alignof $(CONAN_INCLUDE_DIRS) $(CONAN_DEFINES) -Wno-implicit-function-declaration' "
            f"LDFLAGS='$(CONAN_LIB_DIRS)'"
        )

        conandeps_mk = Path(self.build_folder) / "generators" / "conandeps.mk"

        return f"{vars} make -f {conandeps_mk} -f Makefile {' '.join(targets)}"
