(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (blocked ?x)
    (ispoint ?x)
    (headsnake ?x)
    (tailsnake ?x)
    (spawn ?x)
    (ISADJACENT ?x ?y)
    (NEXTSPAWN ?x ?y)
    (nextsnake ?x ?y)
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
        (not (headsnake ?head))
        (headsnake ?newhead)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (nextsnake ?newhead ?head)
    )
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
    )
    :effect
    (and
        (not (headsnake ?head))
        (headsnake ?newhead)
        (blocked ?newhead)
        (nextsnake ?newhead ?head)
        (not (tailsnake ?tail))
        (not (blocked ?tail))
        (tailsnake ?newtail)
        (not (nextsnake ?newtail ?tail))
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
        (spawn ?spawnpoint)
        (not (= ?spawnpoint dummypoint))
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
    )
    :effect
    (and
        (not (headsnake ?head))
        (headsnake ?newhead)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (nextsnake ?newhead ?head)
        (not (spawn ?spawnpoint))
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
    )
)
)