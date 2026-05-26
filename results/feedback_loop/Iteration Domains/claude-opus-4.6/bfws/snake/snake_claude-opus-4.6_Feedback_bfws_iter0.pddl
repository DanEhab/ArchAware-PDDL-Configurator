(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (blocked ?x)
    (ispoint ?x)
    (spawn ?x)
    (NEXTSPAWN ?x ?y)
    (ISADJACENT ?x ?y)
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
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
(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
        (not (ispoint ?newhead))
        (not (headsnake ?head))
        (not (spawn ?spawnpoint))
    )
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (tailsnake ?newtail)
        (blocked ?newhead)
        (not (headsnake ?head))
        (not (tailsnake ?tail))
        (not (nextsnake ?newtail ?tail))
        (not (blocked ?tail))
    )
)
)