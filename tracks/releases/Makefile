PYTHON ?= python3
TRACK  := $(notdir $(CURDIR))
PKG    := $(abspath $(CURDIR)/../../scripts)
RUN    := PYTHONPATH=$(PKG) $(PYTHON) -m

.PHONY: install collect normalize score report-daily report-weekly prune update weekly

install:
	$(PYTHON) -m pip install -r ../../requirements.txt

collect:
	$(RUN) awsdd.collect_rss --track $(TRACK)
	$(RUN) awsdd.collect_github --track $(TRACK)

normalize:
	$(RUN) awsdd.normalize --track $(TRACK)

score:
	$(RUN) awsdd.score --track $(TRACK)

report-daily:
	$(RUN) awsdd.report --track $(TRACK) --mode daily

report-weekly:
	$(RUN) awsdd.report --track $(TRACK) --mode weekly

prune:
	bash ../../scripts/prune.sh .

update: collect normalize score report-daily prune
weekly: collect normalize score report-weekly prune
