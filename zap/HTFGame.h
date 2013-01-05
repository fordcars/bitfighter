//-----------------------------------------------------------------------------------
//
// Bitfighter - A multiplayer vector graphics space game
// Based on Zap demo released for Torque Network Library by GarageGames.com
//
// Derivative work copyright (C) 2008-2009 Chris Eykamp
// Original work copyright (C) 2004 GarageGames.com, Inc.
// Other code copyright as noted
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful (and fun!),
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//
//------------------------------------------------------------------------------------
#ifndef _HTFGAMETYPE_H_
#define _HTFGAMETYPE_H_

#include "gameType.h"


namespace Zap
{

class HTFGameType : public GameType
{
   typedef GameType Parent;
   static StringTableEntry aString;
   static StringTableEntry theString;

   enum {
      ScoreTime = 5000,    // Time flag is in your zone to get points for your team
   };
public:
   HTFGameType();    // Constructor

   bool isFlagGame() const;

   // Server only
   void addFlag(FlagItem *flag);


   // Note -- neutral or enemy-to-all robots can't pick up the flag!!!  When we add robots, this may be important!!!
   void shipTouchFlag(Ship *theShip, FlagItem *theFlag);

   void itemDropped(Ship *ship, MoveItem *item, MountableItem::Dismount_Mode dismountMode);

   void shipTouchZone(Ship *s, GoalZone *z);


   void idle(BfObject::IdleCallPath path, U32 deltaT);

   // Same code as in retrieveGame, CTF
   void performProxyScopeQuery(BfObject *scopeObject, ClientInfo *clientInfo);

   void renderInterfaceOverlay(bool scoreboardVisible);

   GameTypeId getGameTypeId() const;
   const char *getShortName() const;
   const char *getInstructionString() const;
   bool isTeamGame() const;
   bool canBeTeamGame() const;
   bool canBeIndividualGame() const;

   // What does a particular scoring event score?
   S32 getEventScore(ScoringGroup scoreGroup, ScoringEvent scoreEvent, S32 data);

   TNL_DECLARE_CLASS(HTFGameType);
};

};

#endif
