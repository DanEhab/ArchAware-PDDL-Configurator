(define (domain ricochet-robots)
(:requirements :strips :typing :negative-preconditions)

(:types
    robot - object
    cell - object
    direction - object
)

(:predicates
    (at ?r - robot ?c - cell)
    (free ?c - cell)
    (nothing-is-moving)
    (is-moving ?r - robot ?dir - direction)
    (NEXT ?c - cell ?cnext - cell ?dir - direction)
    (BLOCKED ?c - cell ?dir - direction)
)

(:action step
    :parameters (?r - robot ?cfrom - cell ?cto - cell ?dir - direction)
    :precondition
        (and
            (at ?r ?cfrom)
            (free ?cto)
            (is-moving ?r ?dir)
            (NEXT ?cfrom ?cto ?dir)
            (not (BLOCKED ?cfrom ?dir))
        )
    :effect
        (and
            (at ?r ?cto)
            (free ?cfrom)
            (not (at ?r ?cfrom))
            (not (free ?cto))
        )
)

(:action go
    :parameters (?r - robot ?dir - direction)
    :precondition
        (and
            (nothing-is-moving)
        )
    :effect
        (and
            (is-moving ?r ?dir)
            (not (nothing-is-moving))
        )
)

(:action stop-at-barrier
    :parameters (?r - robot ?cat - cell ?dir - direction)
    :precondition
        (and
            (at ?r ?cat)
            (is-moving ?r ?dir)
            (BLOCKED ?cat ?dir)
        )
    :effect
        (and
            (nothing-is-moving)
            (not (is-moving ?r ?dir))
        )
)

(:action stop-at-robot
    :parameters (?r - robot ?cat - cell ?cnext - cell ?dir - direction)
    :precondition
        (and
            (at ?r ?cat)
            (not (free ?cnext))
            (is-moving ?r ?dir)
            (NEXT ?cat ?cnext ?dir)
        )
    :effect
        (and
            (nothing-is-moving)
            (not (is-moving ?r ?dir))
        )
)
)