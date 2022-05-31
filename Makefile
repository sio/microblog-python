SETUP_PY=setup.cfg
include Makefile.venv


ACTION=\
  help\


.PHONY: $(ACTION)
$(ACTION): | venv
	$(VENV)/microblog $@ $(MICROBLOG_ARGS)


.PHONY: test
test: $(VENV)/tox
	$(VENV)/tox $(TOX_ARGS)


.PHONY: clean
clean:
	git clean -idx
