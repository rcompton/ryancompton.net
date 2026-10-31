# The resume needs LuaLaTeX for the florilegium margin (vendored in florilegium/).
#   make
# No TeX installed? Build kevinraymond/florilegium's tools/Dockerfile as florilegium-tex, then
#   make RUN="docker run --rm -v $$PWD:/work -w /work florilegium-tex"
export TEXINPUTS := ./florilegium//:
export LUAINPUTS := ./florilegium//:

ryan_compton_resume.pdf: ryan_compton_resume.tex res.cls $(wildcard florilegium/*)
	$(RUN) env TEXINPUTS=$(TEXINPUTS) LUAINPUTS=$(LUAINPUTS) lualatex -interaction=nonstopmode ryan_compton_resume.tex
