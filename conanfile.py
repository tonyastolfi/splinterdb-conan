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
        #"libaio/[>=0.3]",
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
        try:
            git.get_commit()
        except ConanException:
            git.clone(url="https://github.com/vmware/splinterdb", target=".")

    def build(self):
        print(f"source_folder={self.source_folder}")
        print(f"build_folder={self.build_folder}")

        splinter_build_modes = {
            "Debug": "debug",
            "Release": "release",
            "RelWithDebInfo": "optimized-debug",
        }

        vars = (
            f"BUILD_MODE={splinter_build_modes[str(self.settings.build_type)]} "
            f"BUILD_ROOT={self.build_folder} "
            f"INSTALL_PATH={self.package_folder} "
            f"CC=gcc-12.2.0 "
            f"LD=gcc-12.2.0 "
            f"CONAN_INCLUDE_DIR_FLAG=-I "
            f"CONAN_DEFINE_FLAG=-D "
            f"CONAN_LIB_DIR_FLAG=-L "
            f"CFLAGS='-std=gnu2x $(CONAN_INCLUDE_DIRS) $(CONAN_DEFINES) -Wno-implicit-function-declaration' "
            f"LDFLAGS='$(CONAN_LIB_DIRS)'"
        )

        conandeps_mk = Path(self.build_folder) / "generators" / "conandeps.mk"

        run_tests = ""
        if not self.conf.get("user.build:skip_run_tests", default=False):
            run_tests = "run-tests"
        
        self.run(command=f"{vars} make -f {conandeps_mk} -f Makefile clean all {run_tests}",
                 cwd=self.source_folder)
