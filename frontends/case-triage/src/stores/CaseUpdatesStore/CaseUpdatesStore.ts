// Recidiviz - a data platform for criminal justice reform
// Copyright (C) 2021 Recidiviz, Inc.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// =============================================================================
import { makeAutoObservable, remove, runInAction, set } from "mobx";
import moment from "moment";
import {
  trackPersonActionRemoved,
  trackPersonActionTaken,
} from "../../analytics";
import API from "../API";
import ClientsStore, { Client } from "../ClientsStore";
import UserStore from "../UserStore";
import {
  CaseUpdate,
  CaseUpdateActionType,
  CaseUpdateStatus,
} from "./CaseUpdates";

interface CaseUpdatesStoreProps {
  api: API;
  clientsStore: ClientsStore;
  userStore: UserStore;
}

class CaseUpdatesStore {
  api: API;

  isLoading: boolean;

  clientsStore: ClientsStore;

  userStore: UserStore;

  constructor({ api, clientsStore, userStore }: CaseUpdatesStoreProps) {
    makeAutoObservable(this);

    this.api = api;
    this.isLoading = false;
    this.clientsStore = clientsStore;
    this.userStore = userStore;
  }

  async recordAction(
    client: Client,
    actionType: CaseUpdateActionType,
    comment?: string
  ): Promise<void> {
    this.isLoading = true;

    if (!this.userStore.getTokenSilently) {
      return;
    }

    runInAction(() => {
      set(client, "caseUpdates", {
        ...client.caseUpdates,
        [actionType]: {
          actionTs: moment().format(),
          actionType,
          comment: null,
          status: CaseUpdateStatus.IN_PROGRESS,
        },
      });
    });

    let response: CaseUpdate;
    try {
      response = await this.api.post<CaseUpdate>("/api/case_updates", {
        personExternalId: client.personExternalId,
        actionType,
        comment,
      });
    } catch (error) {
      runInAction(() => remove(client.caseUpdates, actionType));
      this.isLoading = false;
      throw error;
    }

    runInAction(() => {
      set(client, "caseUpdates", {
        ...client.caseUpdates,
        [actionType]: response,
      });
    });

    trackPersonActionTaken(client, actionType);

    this.isLoading = false;
  }

  async removeAction(
    client: Client,
    updateId: string,
    actionType: CaseUpdateActionType
  ): Promise<void> {
    this.isLoading = true;

    if (!this.userStore.getTokenSilently) {
      return;
    }

    const originalAction = client.caseUpdates[actionType];
    runInAction(() => {
      remove(client.caseUpdates, actionType);
    });

    try {
      await this.api.delete(`/api/case_updates/${updateId}`);
    } catch (error) {
      runInAction(() =>
        set(client, "caseUpdates", {
          ...client.caseUpdates,
          [actionType]: originalAction,
        })
      );
      this.isLoading = false;
      throw error;
    }
    trackPersonActionRemoved(client, updateId, actionType);

    this.isLoading = false;
  }

  async toggleAction(
    client: Client,
    eventType: CaseUpdateActionType,
    completedAction: boolean
  ): Promise<void> {
    if (completedAction) {
      return this.recordAction(client, eventType);
    }
    const updateId = client.caseUpdates[eventType]?.updateId;

    if (!updateId) {
      return Promise.reject();
    }

    return this.removeAction(client, updateId, eventType);
  }
}

export default CaseUpdatesStore;
