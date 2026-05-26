(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (tailsnake ?x)
    (headsnake ?x)
    (blocked ?x)
    (ispoint ?x)
    (spawn ?x)
    (nextsnake ?x ?y)
    (ISADJACENT ?x ?y)
    (NEXTSPAWN ?x ?y)
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
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
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (ISADJACENT ?head ?newhead)
        (spawn dummypoint)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (blocked ?newhead)
        (not (ispoint ?newhead))
    )
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (ISADJACENT ?head ?newhead)
        (spawn ?spawnpoint)
        (not (= ?spawnpoint dummypoint))
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (ispoint ?spawnpoint)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
    )
)

)