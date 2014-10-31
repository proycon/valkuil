CC=gcc
CFLAGS=-O2 -Wall -g -I.
DEPS = sockhelp.h
OBJ = sockhelp.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

all: confusible_checker confusible_checker_error d-dt_checker t-dt_checker d-t_checker tte-tten_checker t_checker lexicon_checker split_checker runon_checker wopr_checker garbage_checker soundalike_checker errorlist_checker wiki_checker aspell_checker

punc-recase_checker: punc-recase_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

confusible_checker: confusible_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

confusible_checker_error: confusible_checker_error.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

d-dt_checker: d-dt_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

t-dt_checker: t-dt_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

d-t_checker: d-t_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

tte-tten_checker: tte-tten_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

t_checker: t_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

lexicon_checker: lexicon_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

split_checker: split_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

runon_checker: runon_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

wopr_checker: wopr_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

garbage_checker: garbage_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

soundalike_checker: soundalike_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

errorlist_checker: errorlist_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

wiki_checker: wiki_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

aspell_checker: aspell_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

.PHONY: clean

clean:
	rm -f *.o core punc-recase_checker confusible_checker confusible_checker_error d-dt_checker d-t_checker tte-tten_checker t_checker lexicon_checker split_checker runon_checker wopr_checker garbage_checker soundalike_checker errorlist_checker wiki_checker aspell_checker
