TRACKS := iam security whats-new releases

.PHONY: install update weekly new-track new-deep-dive

install:
	@for t in $(TRACKS); do echo "=== install: $$t ==="; $(MAKE) -C tracks/$$t install || exit $$?; done

update:
	@for t in $(TRACKS); do echo "=== update: $$t ==="; $(MAKE) -C tracks/$$t update || exit $$?; done

weekly:
	@for t in $(TRACKS); do echo "=== weekly: $$t ==="; $(MAKE) -C tracks/$$t weekly || exit $$?; done

new-track:
	@test -n "$(NAME)" || (echo "NAME=<track-name> required" >&2; exit 1)
	bash scripts/new-track.sh "$(NAME)"

new-deep-dive:
	@test -n "$(TRACK)" || (echo "TRACK=<track> required" >&2; exit 1)
	@test -n "$(TOPIC)" || (echo "TOPIC=<topic> required" >&2; exit 1)
	bash scripts/new-deep-dive.sh "$(TRACK)" "$(TOPIC)"
