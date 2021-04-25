CC=gcc

simple-data-race: simple-data-race.c
	$(CC) -pthread -o simple-data-race simple-data-race.c

.PHONY: clean

clean:
	rm simple-data-race
