(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (spawn ?x)
    (ispoint ?x)
    (NEXTSPAWN ?x ?y)
    (blocked ?x)
    (ISADJACENT ?x ?y)
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
)
(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (spawn ?spawnpoint)
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (spawn ?spawnpoint))
        (not (ispoint ?newhead))
        (not (headsnake ?head))
    )
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (tailsnake ?newtail)
        (not (headsnake ?head))
        (not (tailsnake ?tail))
        (not (blocked ?tail))
        (not (nextsnake ?newtail ?tail))
    )
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (spawn dummypoint)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (not (headsnake ?head))
    )
)
)