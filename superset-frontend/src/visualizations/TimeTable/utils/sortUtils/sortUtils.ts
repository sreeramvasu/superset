/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import type { ColumnConfig, Entry } from '../../types';
import { calculateCellValue } from '../valueCalculations/valueCalculations';

/**
 * Both ValueCell and Sparkline cells pass React elements to the sorter.
 * ValueCell provides the precomputed value directly, while Sparkline provides
 * the data required to calculate it.
 */
interface SortableCell {
  props?: {
    value?: number | null;
    valueField?: string;
    column?: ColumnConfig;
    entries?: Entry[];
  };
}

/** Minimal shape of the react-table row required for sorting. */
interface SortableRow {
  values?: Record<string, SortableCell | undefined>;
}

type SortableValue = number | string | null | undefined;

/**
 * Coerces a cell value to a finite number, or null when it is not numeric.
 */
function toComparableNumber(value: SortableValue): number | null {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return num === null || num === undefined || Number.isNaN(num) ? null : num;
}

/**
 * Simple numeric value comparison that handles null, undefined, and mixed types
 * @param a - First value to compare
 * @param b - Second value to compare
 * @param nanTreatment - How to treat NaN values
 * @returns Numeric comparison result
 */
function compareValues(
  a: SortableValue,
  b: SortableValue,
  nanTreatment: 'asSmallest' | 'asLargest' | 'alwaysLast' = 'asSmallest',
): number {
  const numA = toComparableNumber(a);
  const numB = toComparableNumber(b);

  if (numA === null && numB === null) return 0;
  if (numA === null) return nanTreatment === 'asSmallest' ? -1 : 1;
  if (numB === null) return nanTreatment === 'asSmallest' ? 1 : -1;

  return numA - numB;
}

/**
 * Sorts table rows with mixed data types for react-table.
 *
 * @param rowA - First row to compare
 * @param rowB - Second row to compare
 * @param columnId - Column identifier for sorting
 * @returns Numeric comparison result for react-table
 * react-table handles the asc/desc direction flip internally after calling
 * this function, so we only return the raw comparison result.
 */
export function sortNumberWithMixedTypes(
  rowA: SortableRow,
  rowB: SortableRow,
  columnId: string,
) {
  const cellA = rowA.values?.[columnId];
  const cellB = rowB.values?.[columnId];

  const propsA = cellA?.props;
  const propsB = cellB?.props;

  if (!propsA || !propsB) {
    return 0;
  }

  // ValueCell already provides the computed value.
  if ('value' in propsA && 'value' in propsB) {
    return compareValues(propsA.value, propsB.value, 'asSmallest');
  }

  // Sparkline still needs calculation.
  const reversedEntriesA = propsA.entries?.slice().reverse();
  const reversedEntriesB = propsB.entries?.slice().reverse();

  if (
    !reversedEntriesA ||
    !reversedEntriesB ||
    !propsA.valueField ||
    !propsA.column ||
    !propsB.valueField ||
    !propsB.column
  ) {
    return 0;
  }

  const { value: valueA } = calculateCellValue(
    propsA.valueField,
    propsA.column,
    reversedEntriesA,
  );

  const { value: valueB } = calculateCellValue(
    propsB.valueField,
    propsB.column,
    reversedEntriesB,
  );

  return compareValues(valueA, valueB, 'asSmallest');
}
