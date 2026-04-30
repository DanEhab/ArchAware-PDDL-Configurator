(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (ISADJACENT ?x ?y)
    (blocked ?x)
    (ispoint ?x)
    (spawn ?x)
    (NEXTSPAWN ?x ?y)
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (tailsnake ?tail)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (nextsnake ?newtail ?tail)
    )
    :effect
    (and
        (headsnake ?newhead)
        (not (headsnake ?head))
        (nextsnake ?newhead ?head)
        (tailsnake ?newtail)
        (not (tailsnake ?tail))
        (not (nextsnake ?newtail ?tail))
        (blocked ?newhead)
        (not (blocked ?tail))
    )
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (spawn dummypoint)
    )
    :effect
    (and
        (headsnake ?newhead)
        (not (headsnake ?head))
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (ispoint ?newhead))
    )
)
(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (not (= ?spawnpoint dummypoint))
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
    )
    :effect
    (and
        (headsnake ?newhead)
        (not (headsnake ?head))
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (ispoint ?spawnpoint)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
    )
)
)