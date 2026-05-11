(define (domain ricochet-robots)
(:requirements :strips :typing :negative-preconditions)

(:types
    robot - object
    cell - object
    direction - object
)

(:predicates
    ;; No robot is located in the cell ?c
    (free ?c - cell)
    ;; Robot ?r is located in the cell ?c
    (at ?r - robot ?c - cell)
    ;; ?cnext is right next to ?c in the direction of ?dir
    (NEXT ?c - cell ?cnext - cell ?dir - direction)
    ;; moving from ?c in the direction ?dir is blocked
    (BLOCKED ?c - cell ?dir - direction)
    ;; No robot is moving anywhere
    (nothing-is-moving)
    ;; Robot ?r is moving in the direction ?dir
    (is-moving ?r - robot ?dir - direction)
)

;; Make one step from the cell ?cfrom to the cell ?cto with the robot ?r
;; Robot is allowed to make the step only if it is the (only) one currently
;; moving, and it is moving in the direction ?dir
(:action step
    :parameters (?r - robot ?cfrom - cell ?cto - cell ?dir - direction)
    :precondition
        (and
            (at ?r ?cfrom)
            (is-moving ?r ?dir)
            (NEXT ?cfrom ?cto ?dir)
            (free ?cto)
            (not (BLOCKED ?cfrom ?dir))
        )
    :effect
        (and
            (not (at ?r ?cfrom))
            (at ?r ?cto)
            (free ?cfrom)
            (not (free ?cto))
        )
)

;; Starts movement of the robot ?r in the direction ?dir
(:action go
    :parameters (?r - robot ?dir - direction)
    :precondition
        (and
            (nothing-is-moving)

            ;; If we want to make sure that the robot can actually make a step
            ;; in the specified direction, then we need to add the following
            ;; (and the corresponding parameters ?cfrom and ?cto):
            ;;
            ;; (at ?r ?cfrom)
            ;; (NEXT ?cfrom ?cto ?dir)
            ;; (free ?cto)
            ;; (not (BLOCKED ?cfrom ?dir))
        )
    :effect
        (and
            (is-moving ?r ?dir)
            (not (nothing-is-moving))
        )
)

;; Stopping of the robot is split between
;; (i) stop-at-barrier which stops the robot if it cannot move further due to
;;     a barrier expressed with (BLOCKED ...) predicate
;; (ii) stop-at-robot which stops the robot if the next step is blocked by
;;      another robot
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
            (not (is-moving ?r ?dir))
            (nothing-is-moving)
        )
)

(:action stop-at-robot
    :parameters (?r - robot ?cat - cell ?cnext - cell ?dir - direction)
    :precondition
        (and
            (at ?r ?cat)
            (is-moving ?r ?dir)
            (NEXT ?cat ?cnext ?dir)
            (not (free ?cnext))
        )
    :effect
        (and
            (not (is-moving ?r ?dir))
            (nothing-is-moving)
        )
)
)