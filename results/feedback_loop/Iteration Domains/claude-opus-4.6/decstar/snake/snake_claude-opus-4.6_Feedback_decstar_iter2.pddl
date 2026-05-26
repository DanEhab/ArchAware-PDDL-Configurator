(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (ISADJACENT ?x ?y)
    (NEXTSPAWN ?x ?y)
    (nextsnake ?x ?y)
    (headsnake ?x)
    (tailsnake ?x)
    (ispoint ?x)
    (blocked ?x)
    (spawn ?x)
)
(:action move
    :parameters (?newhead ?head ?tail ?newtail)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (tailsnake ?newtail)
        (not (tailsnake ?tail))
        (not (blocked ?tail))
        (not (nextsnake ?newtail ?tail))
    )
)
(:action move-and-eat-spawn
    :parameters (?newhead ?head ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (not (= ?spawnpoint dummypoint))
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
        (ispoint ?spawnpoint)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
    )
)
(:action move-and-eat-no-spawn
    :parameters (?newhead ?head)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (spawn dummypoint)
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
    )
)
)