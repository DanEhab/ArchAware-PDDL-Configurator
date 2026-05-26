(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (tailsnake ?x)
    (spawn ?x)
    (ispoint ?x)
    (headsnake ?x)
    (NEXTSPAWN ?x ?y)
    (nextsnake ?x ?y)
    (ISADJACENT ?x ?y)
    (blocked ?x)
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (ispoint ?newhead)
        (spawn dummypoint)
        (not (blocked ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
        (blocked ?newhead)
    )
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (ispoint ?newhead))
        (not (blocked ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (tailsnake ?tail))
        (not (nextsnake ?newtail ?tail))
        (tailsnake ?newtail)
        (blocked ?newhead)
        (not (blocked ?tail))
    )
)
(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (ispoint ?newhead)
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
        (not (blocked ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (ispoint ?spawnpoint)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
        (not (ispoint ?newhead))
        (blocked ?newhead)
    )
)
)